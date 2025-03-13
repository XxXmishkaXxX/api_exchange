from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.order import Order

class OrderService:
    
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    async def get_list_order(user_data: dict):
        pass

    async def create_order(user_data: dict, order: Order):
        pass

    async def get_order(user_data: dict, order_id: int):
        pass

    async def cancel_order(user_data: dict, order_id: int):
        pass


def get_order_servcice(session: AsyncSession = Depends(get_db)):
    repository = OrderRepository(session)
    return OrderService(repository)
