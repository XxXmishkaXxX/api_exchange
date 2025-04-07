import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.repositories.order_repo import OrderRepository
from app.services.wallet_client import wallet_client
from app.repositories.asset_repo import AssetRepository
from app.models.asset import Asset


class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers, group_id=group_id)

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

    def __init__(self, bootstrap_servers: str, group_id: str):
        super().__init__("orders_update", bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        order_id = int(data["order_id"])
        user_id = int(data["user_id"])
        status = str(data["status"])
        await self.change_order_status(order_id, user_id, status)

    async def change_order_status(self, order_id: int, user_id: int, status: str):
        async for session in get_db():
            order_repo = OrderRepository(session)
            order = await order_repo.get(order_id, user_id)
            if order:
                await order_repo.update(order, {"status": status})


class AssetConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки тикеров.
    """

    def __init__(self, bootstrap_servers: str, group_id: str):
        super().__init__("tickers", bootstrap_servers, group_id)

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

    async def remove_asset_from_redis_and_db(self, ticker: str):
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.delete(asset_key)
            await self.log_message("Удалён актив из Redis", ticker=ticker)

        async for session in get_db():
            repo = AssetRepository(session)
            await repo.delete(ticker)
            await self.log_message("Удалён актив из DB", ticker=ticker)


class ChangeBalanceConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки изменений баланса.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic=topic, bootstrap_servers=bootstrap_servers, group_id=group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode('utf-8'))
        user_id = data["user_id"]
        asset_id = data["asset_id"]
        ticker = data["ticker"]
        amount = int(data["amount"])
        locked = int(data["locked"])

        balance_key = f"user:{user_id}:asset:{ticker}"

        async with redis_pool.connection() as redis:
            exists = await redis.exists(balance_key)

            if not exists:
                await self.initialize_balance(user_id, ticker, balance_key)
            else:
                await self.update_balance(redis, balance_key, amount, locked)

    async def initialize_balance(self, user_id: int, ticker: str, balance_key: str):
        wallet_data = await wallet_client.get_balance(user_id, ticker)
        if wallet_data is None:
            logger.warning(f"No wallet data found for user={user_id}, asset={ticker}")
            return

        async with redis_pool.connection() as redis:
            await redis.hset(balance_key, mapping={
                "amount": int(wallet_data["amount"]),
                "locked": int(wallet_data["locked"])
            })
            await self.log_message("INIT", user_id=user_id, asset=ticker, amount=wallet_data["amount"], locked=wallet_data["locked"])

    async def update_balance(self, redis, balance_key: str, amount: int, locked: int):
        await redis.hset(balance_key, mapping={
            "amount": amount,
            "locked": locked
        })
        await self.log_message("UPDATE", amount=amount, locked=locked)



# Инициализация потребителей
change_balance_consumer = ChangeBalanceConsumer("change_balance", settings.BOOTSTRAP_SERVERS, group_id=None)
order_status_consumer = OrderStatusConsumer(settings.BOOTSTRAP_SERVERS, group_id=None)
asset_consumer = AssetConsumer(settings.BOOTSTRAP_SERVERS, group_id="orders_group")


