import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.services.order import get_order_service, OrderService


class KafkaConsumerService:
    def __init__(self, bootstrap_servers: str, order_service: OrderService):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer("order_updates", bootstrap_servers=self.bootstrap_servers)
        self.order_service = order_service

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()
    
    async def consume_messages(self):
        async for message in self.consumer:
            data = json.loads(message.value.decode("utf-8"))
            order_id = int(data["order_id"])
            user_id = int(data["user_id"])
            status = str(data["status"])
            await self.order_service.change_order_status(order_id, user_id, status)

service = get_order_service()

consumer_service = KafkaConsumerService(settings.BOOTSTRAP_SERVERS,
                                order_service=service)