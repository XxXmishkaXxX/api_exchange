import json
from uuid import UUID
from typing import AsyncGenerator

from app.core.config import settings
from app.kafka.producers.base_producer import BaseKafkaProducerService


class SendUserEventProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        super().__init__(topic, bootstrap_servers)

    async def send_event(self, user_id: UUID, event: str):
        data = {
            "user_id": str(user_id),
            "event": event
        }

        message = json.dumps(data)

        await self.send_message(message.encode("utf-8"))


user_event_producer = SendUserEventProducerService(topic=settings.USER_EVENTS_TOPIC,
                                                       bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_user_event_producer() -> AsyncGenerator[SendUserEventProducerService, None]:
    yield user_event_producer