import json

from app.kafka.consumers.base_consumer import BaseKafkaConsumerService
from app.db.database import get_db, redis_pool
from app.repositories.asset_repo import AssetRepository
from app.models.asset import Asset
from app.core.config import settings

class AssetConsumerService(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки тикеров.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        action = data.get("action")
        asset_id = data.get("asset_id")
        ticker = data.get("ticker")
        name = data.get("name")

        if action == "ADD" and asset_id and ticker and name:
            await self.add_asset_to_redis_and_db(asset_id, ticker, name)
        elif action == "REMOVE" and ticker:
            await self.remove_asset_from_redis_and_db(ticker)

    async def add_asset_to_redis_and_db(self, asset_id: int, ticker: str, name: str):
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.hset(asset_key, mapping={"asset_id": asset_id, "name": name})
            await self.log_message("Добавлен актив в Redis", ticker=ticker, name=name)

        async for session in get_db():
            repo = AssetRepository(session)
            asset = Asset(id=asset_id, name=name, ticker=ticker)
            await repo.create(asset)
            await self.log_message("Добавлен актив в DB", ticker=ticker, name=name)
            break

    async def remove_asset_from_redis_and_db(self, ticker: str):
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.delete(asset_key)
            await self.log_message("Удалён актив из Redis", ticker=ticker)

        async for session in get_db():
            repo = AssetRepository(session)
            await repo.delete(ticker)
            await self.log_message("Удалён актив из DB", ticker=ticker)
            break



asset_consumer = AssetConsumerService(
    settings.ASSET_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="orders_assets_group"
)
