from uuid import UUID
from typing import AsyncGenerator

from app.core.config import settings
from app.kafka.producers.base_producer import BaseKafkaProducerService


class LockAssetsKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        super().__init__(bootstrap_servers, topic=topic)

    async def lock_assets(self, correlation_id, user_id: UUID, asset_id: int, ticker: str, amount: int) -> None:
        data = {
            "correlation_id": correlation_id,
            "user_id": str(user_id),
            "asset_id": asset_id,
            "ticker": ticker,
            "amount": amount
        }
        await self.send_message(data)


lock_assets_producer = LockAssetsKafkaProducerService(settings.LOCK_ASSETS_REQUEST_TOPIC,
                                                      bootstrap_servers=settings.BOOTSTRAP_SERVERS)

async def get_lock_assets_producer() -> AsyncGenerator[LockAssetsKafkaProducerService, None]:
    yield lock_assets_producer