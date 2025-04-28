import json
from typing import Optional
from uuid import UUID
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.repositories.order_repo import OrderRepository
from app.repositories.asset_repo import AssetRepository
from app.models.asset import Asset
from app.services.response_listeners import lock_futures, market_quote_futures


class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, 
                                        bootstrap_servers=self.bootstrap_servers, 
                                        group_id=group_id,
                                        auto_offset_reset="latest",
                                        enable_auto_commit=True)

    async def start(self):
        """Запускает потребителя Kafka."""
        await self.consumer.start()

    async def stop(self):
        """Останавливает потребителя Kafka."""
        await self.consumer.stop()

    async def consume_messages(self):
        """Метод для асинхронного потребления сообщений из Kafka."""
        async for message in self.consumer:
            await self.process_message(message)

    async def process_message(self, message):
        """
        Метод для обработки сообщения. Должен быть реализован в наследниках.
        """
        raise NotImplementedError("Метод process_message должен быть реализован в наследниках")

    async def log_message(self, action: str, **kwargs):
        """
        Логирует информацию о сообщении.
        """
        logger.info(f"{action}: {kwargs}")


class OrderStatusConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки обновлений статуса ордеров.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = self._parse_message(message)
        if data:
            order_id, user_id, status, filled = data
            await self.update_order(order_id, user_id, status, filled)

    def _parse_message(self, message) -> Optional[tuple[UUID, UUID, str, int]]:
        """Парсит сообщение и извлекает необходимые данные."""
        try:
            data = json.loads(message.value.decode("utf-8"))
            order_id = UUID(data["order_id"])
            user_id = UUID(data["user_id"])
            status = str(data["status"])
            filled = int(data["filled"])
            return order_id, user_id, status, filled
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error("Ошибка при парсинге сообщения")

    async def update_order(self, order_id: UUID, user_id: UUID, status: str, filled: int):
        """Обновляет статус и количество заполненных позиций для ордера."""
        async for session in get_db():
            order_repo = OrderRepository(session)
            order = await order_repo.get(order_id, user_id)

            if order:
                updates = {}
                if status:
                    updates["status"] = status
                if filled is not None:
                    updates["filled"] = filled
                
                if updates:
                    await order_repo.update(order, updates)


class AssetConsumer(BaseKafkaConsumerService):
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

class LockResponseKafkaConsumerService(BaseKafkaConsumerService):
    """
    Kafka consumer для обработки ответов о локации средств из wallet-сервиса.
    """

    async def process_message(self, message):
        try:
            value = json.loads(message.value.decode("utf-8"))
            correlation_id = value.get("correlation_id")
            success = value.get("success", False)

            await self.log_message("Получен ответ от wallet", correlation_id=correlation_id, success=success)

            if correlation_id and correlation_id in lock_futures:
                future = lock_futures.pop(correlation_id)
                future.set_result(success)

        except Exception as e:
            await self.log_message("Ошибка обработки сообщения", error=str(e))


class MarketQuoteResponseKafkaConsumerServcie(BaseKafkaConsumerService):
    async def process_message(self, message):
        try:
            value = json.loads(message.value.decode("utf-8"))
            correlation_id = value.get("correlation_id")
            status = value.get("status", "error")

            await self.log_message("Получен маркет-респонс", correlation_id=correlation_id, status=status)

            if correlation_id and correlation_id in market_quote_futures:
                    future = market_quote_futures.pop(correlation_id)
                    future.set_result(value)

        except Exception as e:
            await self.log_message("Ошибка обработки маркет-респонса", error=str(e))


market_quote_response_consumer = MarketQuoteResponseKafkaConsumerServcie(
    settings.MARKET_QUOTE_RESPONSE_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="market_quote_group"
)

lock_response_consumer = LockResponseKafkaConsumerService(
    settings.LOCK_ASSETS_RESPONSE_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="lock_assets_group"
)

order_status_consumer = OrderStatusConsumer(
    settings.OREDER_STATUS_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="orders_group"
)

asset_consumer = AssetConsumer(
    settings.ASSET_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="orders_assets_group"
)



