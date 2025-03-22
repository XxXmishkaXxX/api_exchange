import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.db.database import get_db
from app.repositories.order_repo import OrderRepository


class KafkaConsumerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer("orders_update", bootstrap_servers=self.bootstrap_servers)

    async def change_order_status(self, order_id: int, user_id: int, status: str):
        async for session in get_db():
            order_repo = OrderRepository(session)
            order = await order_repo.get(order_id, user_id)
            if order:
                await order_repo.update(order, {"status": status})

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
            await self.change_order_status(order_id, user_id, status)



consumer_service = KafkaConsumerService(settings.BOOTSTRAP_SERVERS)
