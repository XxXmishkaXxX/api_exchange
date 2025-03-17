import json
from aiokafka import AIOKafkaProducer


from app.core.config import settings
from app.models.order import Order


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_order(self, order: Order):
        message = order.model_dump_json()
        await self.producer.send_and_wait("orders", message.encode("utf-8"))


def get_producer_service():
    return KafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)