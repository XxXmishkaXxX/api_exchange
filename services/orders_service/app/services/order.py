from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderSchema, OrderCancelResponse, OrderCreateResponse, OrderResponse, OrderListResponse
from app.models.order import Order
from app.repositories.ticker_repo import TickerRepository 

class OrderService:
    
    def __init__(self, order_repo: OrderRepository, ticker_repo: TickerRepository):
        self.order_repo = order_repo
        self.ticker_repo = ticker_repo

    
    async def get_order(self, user_data: dict, order_id: int):
        
        user_id = int(user_data.get('sub'))

        order = await self.order_repo.get(order_id, user_id)

        return OrderResponse(order=order)

    async def get_list_order(self, user_data: dict):
        
        user_id = int(user_data.get('sub'))

        orders = await self.order_repo.get_list(user_id)

        orders_data = [OrderSchema.model_validate(order) for order in orders]

        return OrderListResponse(orders=orders_data)

    
    async def create_order(self, user_data: dict, order: OrderSchema):
        
        ticker = await self.ticker_repo.get_ticker_by_id(order.ticker_id)

        if not ticker:
            raise HTTPException(status_code=401, detail="Такого тикер не существует")
        
        order = Order(
            user_id=int(user_data.get("sub")),
            type=order.type,
            status=order.status,
            direction=order.direction,
            ticker_id=ticker.id,
            qty=order.qty,
            price=order.price
        )

        order = await self.order_repo.create(order)

        return OrderCreateResponse(success=True, order_id=order.id)

    async def cancel_order(self, user_data: dict, order_id: int) -> OrderCancelResponse:
        user_id = int(user_data.get('sub')) 
        
        order = await self.order_repo.remove(user_id, order_id)

        if not order:
            raise HTTPException(status_code=401, detail="Такого ордера не существует")

        return OrderCancelResponse(success=True)
    
    async def change_order_status(self, order_id: int, user_id: int, new_status: str):
        order = await self.order_repo.get(order_id, user_id)
        if not order:
            raise ValueError("Order not found.")
        
        if order.status == 'completed' or order.status == 'canceled':
            raise ValueError(f"Order with status {order.status} cannot be changed.")

        await self.order_repo.update(order, new_status)
        return order

def get_order_servcice(session: AsyncSession = Depends(get_db)):
    order_repo = OrderRepository(session)
    ticker_repo = TickerRepository(session)
    return OrderService(order_repo=order_repo, ticker_repo=ticker_repo)
