from typing import AsyncGenerator

from app.core.config import settings
from app.kafka.producers.base_producer import BaseKafkaProducerService

class AssetsKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        super().__init__(bootstrap_servers, topic=topic)

    async def send_asset(self, data: dict):
        await self.send_message(data)
    


assets_producer = AssetsKafkaProducerService(topic=settings.ASSET_TOPIC,
                                        bootstrap_servers=settings.BOOTSTRAP_SERVERS)

async def get_assets_producer() -> AsyncGenerator[AssetsKafkaProducerService, None]:
    yield assets_producer