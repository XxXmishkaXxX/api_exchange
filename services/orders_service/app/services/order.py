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
    
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    async def get_order(self, user_data: dict, order_id: int):
        
        user_id = int(user_data.get('sub'))

        order = await self.order_repo.get(order_id, user_id)

        return OrderResponse(order=order)

    async def get_list_order(self, user_data: dict):
        
        user_id = int(user_data.get('sub'))

        orders = await self.order_repo.get_list(user_id)

        orders_data = [OrderSchema.model_validate(order) for order in orders]

        return OrderListResponse(orders=orders_data)

    
    async def create_order(self, user_data: dict, order: OrderSchema, producer: KafkaProducerService):
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
        user_id = int(user_data.get('sub')) 
        
        order = await self.order_repo.remove(user_id, order_id)

        if not order:
            raise HTTPException(status_code=401, detail="Такого ордера не существует")

        await producer.cancel_order(order_id=order_id, direction=order.direction, ticker_id=order.ticker_id)

        return OrderCancelResponse(success=True)
    

def get_order_service(
    session: AsyncSession = Depends(get_db)
    ):
    order_repo = OrderRepository(session)
    return OrderService(order_repo=order_repo)
