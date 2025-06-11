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

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, auto_offset_reset: str,
                 enable_auto_commit: bool):
        super().__init__(topic, bootstrap_servers, group_id, auto_offset_reset, enable_auto_commit)

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
        try:
            async with get_db() as session:
                repo = AssetRepository(session)
                asset = await repo.get_asset_by_ticker_db(ticker)
                if asset:
                    await repo.change_status(asset, status="ACTIVATE")
                    await self.log_message(f"Актив {ticker} активирован")
                else:
                    asset = Asset(id=asset_id, name=name, ticker=ticker, status="ACTIVATE")
                    asset = await repo.create(asset)
                    await self.log_message("Добавлен актив в DB", ticker=ticker, name=name)

            async with redis_pool.connection() as redis:
                asset_key = f"asset:{ticker}"
                await redis.hset(asset_key, mapping={"asset_id": asset.id, "name": name, "status": "ACTIVATE"})
                await self.log_message("Добавлен актив в Redis", ticker=ticker, name=name)

        except Exception as e:
            await self.log_message(f"Ошибка - {e}")

    async def remove_asset_from_redis_and_db(self, ticker: str):
        try:
            async with redis_pool.connection() as redis:
                asset_key = f"asset:{ticker}"
                await redis.hset(asset_key, mapping={"status": "DEACTIVATE"})
                await self.log_message("Актив деактивирован в Redis", ticker=ticker)

            async with get_db() as session:
                repo = AssetRepository(session)
                asset = await repo.get_asset_by_ticker_db(ticker)
                await repo.change_status(asset=asset, status="DEACTIVATE")
                await self.log_message("Актив деактивирован в DB", ticker=ticker)
        except Exception as e:
            await self.log_message(f"Ошибка - {e}")


assets_consumer = AssetConsumerService(
    settings.ASSET_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="wallet_assets_group2",
    auto_offset_reset="earliest", enable_auto_commit=False
)
