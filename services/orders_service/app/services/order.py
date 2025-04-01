from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, get_redis_connection
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (OrderSchema, 
                               OrderCancelResponse, 
                               OrderCreateResponse, 
                               OrderResponse, 
                               OrderListResponse)
from app.models.order import Order
from app.services.producer import KafkaProducerService

class OrderService:
    """
    Сервис для управления ордерами.

    Этот класс предоставляет методы для создания, получения и отмены ордеров,
    а также для проверки существования ордеров.
    """

    def __init__(self, order_repo: OrderRepository):
        """
        Инициализация сервиса ордеров с репозиторием ордеров.

        Аргументы:
            order_repo (OrderRepository): Репозиторий для взаимодействия с данными ордеров.
        """
        self.order_repo = order_repo

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
        return OrderResponse(order=order)

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
        orders_data = [OrderSchema.model_validate(order) for order in orders]
        return OrderListResponse(orders=orders_data)

    async def create_order(self, user_data: dict, order: OrderSchema, producer: KafkaProducerService) -> OrderCreateResponse:
        """
        Создание нового ордера.

        Аргументы:
            user_data (dict): Данные пользователя, содержащие информацию о пользователе (например, ID).
            order (OrderSchema): Данные ордера, которые нужно создать.
            producer (KafkaProducerService): Сервис для отправки ордера в Kafka.

        Возвращает:
            OrderCreateResponse: Ответ с информацией о созданном ордере.
        """
        async with get_redis_connection() as redis:
            ticker_key = f"ticker:{order.ticker_id}"
            ticker_exists = await redis.exists(ticker_key)
        
        if not ticker_exists:
            raise HTTPException(status_code=401, detail="Такого тикера не существует")

        order = Order(
            user_id=int(user_data.get("sub")),
            type=order.type,
            status="new",
            direction=order.direction,
            ticker_id=order.ticker_id,
            qty=order.qty,
            price=order.price
        )

        order = await self.order_repo.create(order)
        await producer.send_order(order=order)
        return OrderCreateResponse(success=True, order_id=order.id)

    async def cancel_order(self, user_data: dict, order_id: int, producer: KafkaProducerService) -> OrderCancelResponse:
        """
        Отмена ордера.

        Аргументы:
            user_data (dict): Данные пользователя, содержащие информацию о пользователе (например, ID).
            order_id (int): ID ордера для отмены.
            producer (KafkaProducerService): Сервис для отправки информации об отмене ордера в Kafka.

        Возвращает:
            OrderCancelResponse: Ответ, подтверждающий успешную отмену ордера.
        """
        user_id = int(user_data.get('sub')) 
        order = await self.order_repo.remove(user_id, order_id)

        if not order:
            raise HTTPException(status_code=401, detail="Такого ордера не существует")

        await producer.cancel_order(order_id=order_id, direction=order.direction, ticker_id=order.ticker_id)
        return OrderCancelResponse(success=True)


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
    order_repo = OrderRepository(session)
    return OrderService(order_repo=order_repo)
