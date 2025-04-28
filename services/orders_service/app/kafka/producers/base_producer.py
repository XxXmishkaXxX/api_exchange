import json
from uuid import UUID
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings
from app.models.order import Order


class BaseKafkaProducerService:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def send_message(self, data: dict) -> None:
        message = json.dumps(data)
        await self.producer.send_and_wait(self.topic, message.encode("utf-8"))