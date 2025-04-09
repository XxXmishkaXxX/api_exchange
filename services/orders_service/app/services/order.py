import asyncio
import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.database import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (OrderSchema, 
                               OrderCancelResponse, 
                               OrderCreateResponse, 
                               OrderResponse, 
                               OrderListResponse,
                               StatusOrder)
from app.models.order import Order
from app.services.lock_response_listener import lock_futures
from app.services.producer import OrderKafkaProducerService, LockAssetsKafkaProducerService
from app.repositories.asset_repo import AssetRepository
from app.core.logger import logger


class OrderService:
    """
    Сервис для управления ордерами.

    Этот класс предоставляет методы для создания, получения, отмены ордеров, а также для проверки существования ордеров.
    """

    def __init__(self, order_repo: OrderRepository, asset_repo: AssetRepository):
        """
        Инициализация сервиса ордеров с репозиторием ордеров и активов.

        Аргументы:
            order_repo (OrderRepository): Репозиторий для взаимодействия с данными ордеров.
            asset_repo (AssetRepository): Репозиторий для работы с активами.
        """
        self.order_repo = order_repo
        self.asset_repo = asset_repo

    async def get_order(self, user_data: dict, order_id: int) -> OrderResponse:
        """
        Получение конкретного ордера пользователя.

        Аргументы:
            user_data (dict): Данные пользователя, содержащие информацию о пользователе (например, ID).
            order_id (int): ID ордера для получения.

        Возвращает:
            OrderResponse: Ответ, содержащий детали ордера.
        """
        user_id = int(user_data.get('sub'))
        order = await self.order_repo.get(order_id, user_id)
        logger.info(order)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return OrderResponse(
                order_id=order.id,
                user_id=order.user_id,
                status=order.status,
                timestamp=order.updated_at.isoformat(),  
                body=OrderSchema(
                    type=order.type,
                    direction=order.direction,
                    ticker=order.order_asset.ticker,
                    payment_order_ticker=order.payment_asset.ticker,
                    qty=order.qty,
                    price=order.price
                ),
                filled=order.filled
            )

    async def get_list_order(self, user_data: dict) -> OrderListResponse:
        """
        Получение списка ордеров пользователя.

        Аргументы:
            user_data (dict): Данные пользователя, содержащие информацию о пользователе (например, ID).

        Возвращает:
            OrderListResponse: Ответ, содержащий список ордеров.
        """
        user_id = int(user_data.get('sub'))
        orders = await self.order_repo.get_list(user_id)
        
        return OrderListResponse(
            orders=[
                OrderResponse(
                    order_id=order.id,
                    user_id=order.user_id,
                    status=order.status,
                    timestamp=order.updated_at.isoformat(),
                    body=OrderSchema(
                        type=order.type,
                        direction=order.direction,
                        ticker=order.order_asset.ticker,
                        payment_order_ticker=order.payment_asset.ticker,
                        qty=order.qty,
                        price=order.price
                    ),
                    filled=order.filled
                )
                for order in orders
            ]
        )
    # пока не реализовано создание рыночного ордера, из-за незнания цены рынка!
    # пофиксить
    async def create_order(self, user_data: dict, 
                            order: OrderSchema, 
                            prod_order: OrderKafkaProducerService,
                            prod_lock: LockAssetsKafkaProducerService) -> OrderCreateResponse:
        user_id = int(user_data.get("sub"))

        order_asset_id = await self.asset_repo.get_asset_by_ticker(order.ticker)
        payment_asset_id = await self.asset_repo.get_asset_by_ticker(order.payment_ticker)

        if not order_asset_id or not payment_asset_id:
            missing_assets = []
            if not order_asset_id:
                missing_assets.append(f"order asset '{order.ticker}'")
            if not payment_asset_id:
                missing_assets.append(f"payment asset '{order.payment_ticker}'")
            raise HTTPException(
                status_code=404,
                detail=f"Asset(s) not found: {', '.join(missing_assets)}"
            )

        ticker = order.payment_ticker if order.direction == "buy" else order.ticker
        asset_id = payment_asset_id if order.direction == "buy" else order_asset_id
        quantity = int(order.qty * order.price) if order.direction == "buy" else order.qty

        try:
            correlation_id = str(uuid.uuid4())

            await prod_lock.lock_assets(
                user_id=user_id,
                asset_id=asset_id,
                ticker=ticker,
                amount=quantity,
                correlation_id=correlation_id
            )

            success = await self._wait_for_lock_confirmation(correlation_id)

            if not success:
                raise HTTPException(status_code=400, detail=f"Недостаточно средств {ticker}")

        except HTTPException as e:
            logger.error(f"HTTPException: {e.detail}")
            raise e

        except Exception as e:
            logger.error(f"Ошибка при попытке локации активов: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при попытке локации активов: {e}")

        order_entity = Order(
            user_id=user_id,
            type=order.type,
            status=StatusOrder.NEW,
            direction=order.direction,
            qty=order.qty,
            price=order.price,
            order_asset_id=order_asset_id,
            payment_asset_id=payment_asset_id
        )

        order_entity = await self.order_repo.create(order_entity)

        try:
            await prod_order.send_order(
                order.ticker,
                order.payment_ticker,
                order=order_entity
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка отправки ордера в Matching Engine: {e}")

        return OrderCreateResponse(success=True, order_id=order_entity.id)


    async def cancel_order(self, user_data: dict, 
                        order_id: int, 
                        prod_order: OrderKafkaProducerService,) -> OrderCancelResponse:
        """
        Отмена ордера.

        Аргументы:
            user_data (dict): Данные пользователя.
            order_id (int): ID ордера для отмены.
            prod_order (OrderKafkaProducerService): Сервис для отмены ордера в Kafka.
            prod_lock (LockAssetsKafkaProducerService): Сервис для разблокировки активов в Kafka.

        Возвращает:
            OrderCancelResponse: Ответ, подтверждающий отмену ордера.
        """
        user_id = int(user_data.get('sub')) 
        order = await self.order_repo.remove(user_id, order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Такого ордера не существует")

        logger.info(order.order_asset.ticker)
        logger.info(order.payment_asset.ticker)
        await prod_order.cancel_order(order_id=order_id, direction=order.direction, 
                                      order_ticker=order.order_asset.ticker,
                                      payment_ticker=order.payment_asset.ticker)
        
        return OrderCancelResponse(success=True)

    async def _wait_for_lock_confirmation(self, correlation_id: str, timeout: int = 5) -> bool:
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        lock_futures[correlation_id] = future
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            lock_futures.pop(correlation_id, None)
            return False

def get_order_service(
    session: AsyncSession = Depends(get_db)
) -> OrderService:
    """
    Функция для получения экземпляра сервиса ордеров.

    Аргументы:
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        OrderService: Экземпляр сервиса ордеров.
    """
    asset_repo = AssetRepository(session)
    order_repo = OrderRepository(session)
    return OrderService(order_repo=order_repo, asset_repo=asset_repo)
