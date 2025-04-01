import json
from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.models.order import Order


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self):
        """Запуск продюсера Kafka"""
        await self.producer.start()

    async def stop(self):
        """Остановка продюсера Kafka"""
        await self.producer.stop()

    async def send_order(self, order: Order):
        order_data = {
        "action": "add",
        "order_id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "type": order.type,
        "direction": order.direction,
        "ticker_id": order.ticker_id,
        "qty": order.qty,
        "price": order.price,
        }
        message = json.dumps(order_data)
        await self.producer.send_and_wait("orders", message.encode("utf-8"))
    
    async def cancel_order(self, order_id: int, direction: str, ticker_id: int):
        
        data = {"action": "cancel",
                "order_id": order_id,
                "direction": direction,
                "ticker_id": ticker_id}
        
        message = json.dumps(data)
        await self.producer.send_and_wait("orders", message.encode("utf-8"))


producer_service = KafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_producer_service():
    yield producer_service 