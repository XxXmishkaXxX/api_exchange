import json
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.order import Order

class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.order_asset))
            .options(selectinload(Order.payment_asset))
            .filter(Order.id == order_id, Order.user_id == user_id)
        )
        return result.scalars().first()

    async def get_list(self, user_id: UUID) -> Optional[List[Order]]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.order_asset))
            .options(selectinload(Order.payment_asset))
            .filter(Order.user_id == user_id)
        )
        orders = result.scalars().all()
        return orders

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def update(self, order: Order, updated_data: dict) -> Optional[Order]:
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

    async def remove(self, user_id: UUID, order_id: UUID) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.order_asset))
            .options(selectinload(Order.payment_asset))
            .filter(Order.user_id == user_id, Order.id == order_id)
        )
        order = result.scalars().first()
        if order and order.status in ["new", "pending"]:
            await self.db.delete(order)
            await self.db.commit()
        return order
