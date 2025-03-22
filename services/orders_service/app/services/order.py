from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (OrderSchema, 
                               OrderCancelResponse, 
                               OrderCreateResponse, 
                               OrderResponse, 
                               OrderListResponse)
from app.models.order import Order
from app.repositories.ticker_repo import TickerRepository 
from app.services.producer import get_producer_service, KafkaProducerService

class OrderService:
    
    def __init__(self, order_repo: OrderRepository, ticker_repo: TickerRepository, producer: KafkaProducerService):
        self.order_repo = order_repo
        self.ticker_repo = ticker_repo
        self.producer = producer

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
            status="new",
            direction=order.direction,
            ticker_id=ticker.id,
            qty=order.qty,
            price=order.price
        )

        order = await self.order_repo.create(order)

        await self.producer.send_order(order=order)

        return OrderCreateResponse(success=True, order_id=order.id)

    async def cancel_order(self, user_data: dict, order_id: int) -> OrderCancelResponse:
        user_id = int(user_data.get('sub')) 
        
        order = await self.order_repo.remove(user_id, order_id)

        if not order:
            raise HTTPException(status_code=401, detail="Такого ордера не существует")

        return OrderCancelResponse(success=True)
    

def get_order_service(
    session: AsyncSession = Depends(get_db),
    producer: KafkaProducerService = Depends(get_producer_service)
):
    order_repo = OrderRepository(session)
    ticker_repo = TickerRepository(session)
    return OrderService(order_repo=order_repo, ticker_repo=ticker_repo, producer=producer)
