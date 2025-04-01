import json
from aiokafka import AIOKafkaConsumer
from redis import asyncio as aioredis

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, get_redis_connection
from app.repositories.order_repo import OrderRepository


class BaseKafkaConsumerService:
    def __init__(self, topic: str, bootstrap_servers: str):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers)

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()

    async def consume_messages(self):
        async for message in self.consumer:
            await self.process_message(message)

    async def process_message(self, message):
        raise NotImplementedError("Метод process_message должен быть реализован в наследниках")


class OrderStatusConsumer(BaseKafkaConsumerService):
    def __init__(self, bootstrap_servers: str):
        super().__init__("orders_update", bootstrap_servers)

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


class TickerConsumer(BaseKafkaConsumerService):
    def __init__(self, bootstrap_servers: str):
        super().__init__("tickers", bootstrap_servers)
        self.redis = None

    async def start(self):
        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await super().start()

    async def stop(self):
        if self.redis:
            await self.redis.close()
        await super().stop()

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        action = data.get("action")
        ticker_id = data.get("ticker_id")
        symbol = data.get("symbol")
        name = data.get("name")

        if action == "ADD" and ticker_id and symbol and name:
            async with get_redis_connection() as redis:
                ticker_key = f"ticker:{ticker_id}"
                await redis.hset(ticker_key, mapping={"symbol": symbol, "name": name})
                logger.info(f"Добавлен тикер в Redis: {ticker_id} -> {symbol} ({name})")

        elif action == "REMOVE" and ticker_id:
            async with get_redis_connection() as redis:
                ticker_key = f"ticker:{ticker_id}"
                await redis.delete(ticker_key)
                logger.info(f"Удалён тикер из Redis: {ticker_id}")


order_status_consumer = OrderStatusConsumer(settings.BOOTSTRAP_SERVERS)
ticker_consumer = TickerConsumer(settings.BOOTSTRAP_SERVERS)



