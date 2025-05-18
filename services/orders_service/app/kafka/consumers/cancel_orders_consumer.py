import json
from uuid import UUID


from app.db.database import get_db
from app.deps.services import get_order_service
from app.core.config import settings
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService



class CancelAllOrdersUserConsumerServcie(BaseKafkaConsumerService):
    async def process_message(self, message):
        try:
            value = json.loads(message.value.decode("utf-8"))
            user_id = value.get("user_id")
            event = value.get("event")
            if event == "delete":
                await self.log_message("Отмена всех ордеров для пользователя", user_id=user_id)

                async with get_db() as session:
                    service = get_order_service(session=session)
                    await service.cancel_all_orders(user_id)

        except Exception as e:
            await self.log_message("Ошибка обработки маркет-респонса", error=str(e))

cancel_user_orders_consumer = CancelAllOrdersUserConsumerServcie(
    settings.USER_EVENTS_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="orders_users_group"
)
