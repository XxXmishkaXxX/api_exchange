import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.models.order import Order
from app.db.database import redis_pool
from app.core.logger import logger


class OrderRepository:
    """
    Репозиторий для работы с заказами в базе данных.

    Этот класс содержит методы для получения, создания, обновления и удаления заказов.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.
        """
        self.db = session

    async def get(self, order_id: int, user_id: int) -> Optional[Order]:
        """
        Получение заказа по ID и пользователю.

        Аргументы:
            order_id (int): ID заказа.
            user_id (int): ID пользователя.

        Возвращает:
            Optional[Order]: Возвращает заказ, если найден, иначе None.
        """
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.order_asset))
            .options(selectinload(Order.payment_asset))
            .filter(Order.id == order_id, Order.user_id == user_id)
        )
        return result.scalars().first()


    
    async def get_list(self, user_id: int) -> Optional[List[Order]]:
        result = await self.db.execute(
            select(Order)            
            .options(selectinload(Order.order_asset))
            .options(selectinload(Order.payment_asset))
            .filter(Order.user_id == user_id)
        )
        orders = result.scalars().all()

        return orders

    async def create(self, order: Order) -> Order:
        """
        Создание нового заказа.

        Аргументы:
            order (Order): Объект заказа для сохранения.

        Возвращает:
            Order: Сохранённый объект заказа.
        """
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def update(self, order: Order, updated_data: dict) -> Optional[Order]:
        """
        Обновление данных заказа.

        Аргументы:
            order (Order): Объект заказа для обновления.
            updated_data (dict): Словарь с данными для обновления.

        Возвращает:
            Optional[Order]: Возвращает обновлённый заказ, если были изменения, иначе None.
        """
        changes_made = False

        for key, value in updated_data.items():
            if hasattr(order, key) and getattr(order, key) != value:
                setattr(order, key, value)
                changes_made = True

        if changes_made:
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            return order
        return None

    async def remove(self, user_id: int, order_id: int) -> Optional[Order]:
        """
        Удаление заказа.

        Аргументы:
            user_id (int): ID пользователя.
            order_id (int): ID заказа.

        Возвращает:
            Optional[Order]: Возвращает удалённый заказ, если он был найден и удалён, иначе None.
        """
        result = await self.db.execute(
            select(Order).options(selectinload(Order.asset)).
            filter(Order.user_id == user_id, Order.id == order_id)
        )
        order = result.scalars().first()
        if order and order.status in ["new", "pending"]:
            await self.db.delete(order)
            await self.db.commit()
        return order


    async def lock(self, user_id, ticker, amount):
        key = f"user:{user_id}:asset:{ticker}"

        
        async with redis_pool.connection() as redis:
            data = await redis.hgetall(key)

            if data is None:
                return False
            logger.info(data)
            locked = int(data["locked"])
            data["locked"] = amount + locked

            await redis.hset(key, mapping=data)

            return True

    async def unlock(self, user_id, ticker, amount):
        key = f"user:{user_id}:asset:{ticker}"

        async with redis_pool.connection() as redis:
            data = await redis.hgetall(key)

            if data is None:
                return False

            locked = int( data["locked"])
            data["locked"] = locked - amount

            await redis.hset(key, mapping=data)

            return True