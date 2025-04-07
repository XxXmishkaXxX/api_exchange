from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.database import get_db, redis_pool
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (OrderSchema, 
                               OrderCancelResponse, 
                               OrderCreateResponse, 
                               OrderResponse, 
                               OrderListResponse,
                               StatusOrder)
from app.models.order import Order
from app.services.producer import OrderKafkaProducerService, LockAssetsKafkaProducerService
from app.repositories.asset_repo import AssetRepository
from app.services.wallet_client import wallet_client
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
                )
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
                    )
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
        """
        Создание нового ордера.

        Аргументы:
            user_data (dict): Данные пользователя, содержащие информацию о пользователе.
            order (OrderSchema): Схема данных для создания ордера.
            prod_order (OrderKafkaProducerService): Сервис для отправки ордера в Kafka.
            prod_lock (LockAssetsKafkaProducerService): Сервис для блокировки активов в Kafka.

        Возвращает:
            OrderCreateResponse: Ответ, подтверждающий создание ордера.
        """
        user_id = int(user_data.get("sub"))

        order_asset_id = await self.asset_repo.get_asset_by_ticker(order.ticker)
        payment_asset_id = await self.asset_repo.get_asset_by_ticker(order.payment_ticker)
        logger.info(order_asset_id, payment_asset_id)
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

        await self.validate_balance_for_order(user_id, order)
        
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
        
        ticker = order.payment_ticker if order.direction == "buy" else order.ticker
        quantity = int(order.qty * order.price) if order.direction == "buy" else order.qty

        await self.order_repo.lock(user_id, ticker, quantity)
        
        try:
            await prod_order.send_order(order.ticker, order.payment_ticker, order=order_entity)

            if order.direction == "buy":
                await prod_lock.lock_assets(user_id, payment_asset_id, order.payment_ticker, quantity)
            else:
                await prod_lock.lock_assets(user_id, order_asset_id, order.ticker, quantity)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending order to Kafka: {e}")
        
        return OrderCreateResponse(success=True, order_id=order_entity.id)

    async def cancel_order(self, user_data: dict, 
                        order_id: int, 
                        prod_order: OrderKafkaProducerService,
                        prod_lock: LockAssetsKafkaProducerService) -> OrderCancelResponse:
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
        order = await self.order_repo.get(order_id, user_id)

        if not order:
            raise HTTPException(status_code=404, detail="Такого ордера не существует")

        if order.direction == 'buy':
            await self.order_repo.unlock(user_id=user_id, ticker=order.payment_asset.ticker, amount=order.qty * order.price)
        else:
            await self.order_repo.unlock(user_id=user_id, ticker=order.order_asset.ticker, amount=order.qty)

        await prod_order.cancel_order(order_id=order_id, 
                                    asset_id=order.order_asset_id if order.direction == 'sell' else order.payment_asset_id,
                                    direction=order.direction, 
                                    ticker=order.order_asset.ticker if order.direction == 'sell' else order.payment_asset.ticker)
        
        if order.direction == 'buy':
            await prod_lock.unlock_assets(user_id, order.payment_asset_id, order.payment_asset.ticker, order.qty * order.price)
        else:
            await prod_lock.unlock_assets(user_id, order.order_asset_id, order.order_asset.ticker, order.qty)

        return OrderCancelResponse(success=True)

    async def _get_balance(self, user_id: int, ticker: str) -> int:
        """
        Получение баланса пользователя из Redis.
        
        Аргументы:
            user_id (int): ID пользователя для получения баланса.
            ticker (str): Тикер актива.
        
        Возвращает:
            int: Баланс пользователя.
        """
        balance_key = f"user:{user_id}:asset:{ticker}"

        async with redis_pool.connection() as redis:
            user_asset_balance = await redis.hgetall(balance_key)

            if not user_asset_balance:
                data = await wallet_client.get_balance(user_id=user_id, ticker=ticker)
                if data:
                    amount = int(data["amount"])
                    locked = int(data["locked"])
                    await redis.hset(balance_key, mapping={
                        "amount": amount,
                        "locked": locked})
                else:
                    raise HTTPException(status_code=400, detail=f"У вас нет актива - {ticker}, пополните кошелек таким активом")
            else:
                amount = int(user_asset_balance["amount"])
                locked = int(user_asset_balance["locked"])
            
        if amount < locked:
            raise HTTPException(status_code=400, detail="Недостаточно доступных средств для выполнения операции")
        return int(amount)
    
    async def validate_balance_for_order(self, user_id: int, order: OrderSchema):
        """
        Проверка баланса пользователя для выполнения ордера.

        Аргументы:
            user_id (int): ID пользователя.
            order (OrderSchema): Схема ордера, для которого проверяется баланс.

        Исключения:
            HTTPException: Если средств или активов недостаточно.
        """
        if order.direction == "buy":
            balance = await self._get_balance(user_id, order.payment_ticker)
            required_amount = order.qty * order.price
            if balance < required_amount:
                raise HTTPException(status_code=400, detail="Недостаточно средств для выполнения ордера")

        elif order.direction == "sell":
            balance = await self._get_balance(user_id, order.ticker)
            if balance < order.qty:
                raise HTTPException(status_code=400, detail="Недостаточно активов для продажи")


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
