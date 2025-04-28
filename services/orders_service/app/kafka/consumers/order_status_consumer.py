import json
from typing import Optional
from uuid import UUID


from app.core.logger import logger
from app.db.database import get_db
from app.repositories.order_repo import OrderRepository
from app.core.config import settings
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class OrderStatusConsumerService(BaseKafkaConsumerService):
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



order_status_consumer = OrderStatusConsumerService(
    settings.OREDER_STATUS_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="orders_group"
)
