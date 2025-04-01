import json
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings
from app.models.order import Order


class KafkaProducerService:
    """
    Сервис для взаимодействия с Kafka, отправляющий сообщения о заказах.
    
    Этот сервис позволяет отправлять информацию о новых и отменённых ордерах в Kafka.
    """

    def __init__(self, bootstrap_servers: str):
        """
        Инициализация Kafka продюсера.

        Аргументы:
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self) -> None:
        """Запуск продюсера Kafka."""
        await self.producer.start()

    async def stop(self) -> None:
        """Остановка продюсера Kafka."""
        await self.producer.stop()

    async def send_order(self, order: Order) -> None:
        """
        Отправка нового ордера в Kafka.

        Аргументы:
            order (Order): Объект ордера, который будет отправлен в Kafka.
        """
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
    
    async def cancel_order(self, order_id: int, direction: str, ticker_id: int) -> None:
        """
        Отправка отмены ордера в Kafka.

        Аргументы:
            order_id (int): ID ордера.
            direction (str): Направление ордера.
            ticker_id (int): ID тикера.
        """
        data = {
            "action": "cancel",
            "order_id": order_id,
            "direction": direction,
            "ticker_id": ticker_id
        }
        message = json.dumps(data)
        await self.producer.send_and_wait("orders", message.encode("utf-8"))


producer_service = KafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_producer_service() -> AsyncGenerator[KafkaProducerService, None]:
    """
    Асинхронный генератор для получения экземпляра сервиса Kafka продюсера.

    Возвращает:
        KafkaProducerService: Экземпляр сервиса Kafka продюсера.
    """
    yield producer_service
