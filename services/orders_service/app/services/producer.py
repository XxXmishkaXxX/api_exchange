import json
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


class OrderKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, bootstrap_servers: str):
        super().__init__(bootstrap_servers, topic="orders")

    async def send_order(self, order_ticker: str, payment_ticker: str, order: Order) -> None:
        data = {
            "action": "add",
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "type": order.type,
            "direction": order.direction,
            "order_asset_id": order.order_asset_id,
            "payment_asset_id": order.payment_asset_id,
            "order_ticker": order_ticker,
            "payment_ticker": payment_ticker,
            "qty": order.qty,
            "price": order.price,
            "filled": order.filled
        }
        await self.send_message(data)

    async def cancel_order(self, order_id: int, direction: str, order_ticker: str, payment_ticker: str) -> None:
        data = {
            "action": "cancel",
            "order_id": order_id,
            "direction": direction,
            "order_ticker": order_ticker,
            "payment_ticker": payment_ticker
        }
        await self.send_message(data)



class LockAssetsKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, bootstrap_servers: str):
        super().__init__(bootstrap_servers, topic="lock_assets")

    async def lock_assets(self, correlation_id, user_id: int, asset_id: int, ticker: str, amount: int) -> None:
        data = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "asset_id": asset_id,
            "ticker": ticker,
            "amount": amount
        }
        await self.send_message(data)

    async def unlock_assets(self, user_id: int, asset_id: int, ticker: str, amount: int) -> None:
        data = {
            "action": "unlock",
            "user_id": user_id,
            "asset_id": asset_id,
            "ticker": ticker,
            "amount": amount
        }
        await self.send_message(data)


lock_assets_producer = LockAssetsKafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)
order_producer = OrderKafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_order_producer_service() -> AsyncGenerator[OrderKafkaProducerService, None]:
    """
    Асинхронный генератор для получения экземпляра сервиса Kafka продюсера.

    Возвращает:
        OrderKafkaProducerService: Экземпляр сервиса Kafka продюсера.
    """
    yield order_producer


async def get_lock_assets_producer() -> AsyncGenerator[LockAssetsKafkaProducerService, None]:
    yield lock_assets_producer
