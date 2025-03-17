import json
from aiokafka import AIOKafkaConsumer
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.order import get_order_servcice, OrderService
from app.db.database import get_db


class KafkaConsumerService:
    def __init__(self, bootstrap_servers: str, order_service: OrderService):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer("order_updates", bootstrap_servers=self.bootstrap_servers)
        self.order_service = order_service

    async def start(self):
        await self.consumer.start()
        async for message in self.consumer:
            data = json.loads(message.value.decode("utf-8"))
            order_id = int(data["order_id"])
            user_id = int(data["user_id"])
            status = str(data["status"])
            await self.order_service.change_order_status(order_id, user_id, status)

    async def stop(self):
        await self.consumer.stop()

def get_consumer_service(db: AsyncSession = Depends(get_db)):
    order_service = get_order_servcice(db)
    return KafkaConsumerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS, 
                                order_service=order_service)
