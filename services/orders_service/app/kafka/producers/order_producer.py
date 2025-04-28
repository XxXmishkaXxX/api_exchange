import json
from uuid import UUID
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings
from app.models.order import Order
from app.kafka.producers.base_producer import BaseKafkaProducerService


class OrderKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        super().__init__(bootstrap_servers, topic=topic)

    async def send_order(self, order_ticker: str, payment_ticker: str, order: Order) -> None:
        data = {
            "action": "add",
            "order_id": str(order.id),
            "user_id": str(order.user_id),
            "status": order.status,
            "type": order.type,
            "direction": order.direction,
            "order_asset_id": order.order_asset_id,
            "payment_asset_id": order.payment_asset_id,
            "order_ticker": order_ticker,
            "payment_ticker": payment_ticker,
            "qty": order.qty,
            "price": order.price,
            "filled": order.filled
        }
        await self.send_message(data)

    async def cancel_order(self, order_id: UUID, direction: str, order_ticker: str, payment_ticker: str) -> None:
        data = {
            "action": "cancel",
            "order_id": str(order_id),
            "direction": direction,
            "order_ticker": order_ticker,
            "payment_ticker": payment_ticker
        }
        await self.send_message(data)


order_producer = OrderKafkaProducerService(settings.ORDERS_TOPIC,
                                           bootstrap_servers=settings.BOOTSTRAP_SERVERS)

async def get_order_producer() -> AsyncGenerator[OrderKafkaProducerService, None]:
    yield order_producer