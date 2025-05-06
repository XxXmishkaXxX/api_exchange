import json
from uuid import UUID
from typing import AsyncGenerator

from app.core.config import settings
from app.kafka.producers.base_producer import BaseKafkaProducerService


class SendWalletEventProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        """
        Класс для отправки сообщений в тему Kafka с ответом на запрос о блокировке активов.

        Аргументы:
            topic (str): Тема Kafka для отправки ответа.
            bootstrap_servers (str): Список адресов Kafka серверов.
        """
        super().__init__(topic, bootstrap_servers)

    async def send_event(self, user_id: UUID, event: str):
        data = {
            "user_id": str(user_id),
            "event": event
        }

        message = json.dumps(data)

        await self.send_message(message.encode("utf-8"))


wallet_event_producer = SendWalletEventProducerService(topic=settings.WALLET_EVENTS_TOPIC,
                                                       bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_wallet_event_producer() -> AsyncGenerator[SendWalletEventProducerService, None]:
    yield wallet_event_producer