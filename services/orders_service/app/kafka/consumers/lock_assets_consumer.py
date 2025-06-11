import json

from app.kafka.consumers.base_consumer import BaseKafkaConsumerService
from app.services.response_listeners import lock_futures
from app.core.config import settings

class LockResponseKafkaConsumerService(BaseKafkaConsumerService):
    """
    Kafka consumer для обработки ответов о локации средств из wallet-сервиса.
    """

    async def process_message(self, message):
        try:
            value = json.loads(message.value.decode("utf-8"))
            correlation_id = value.get("correlation_id")
            success = value.get("success", False)

            if correlation_id and correlation_id in lock_futures:
                future = lock_futures.pop(correlation_id)
                future.set_result(success)

        except Exception as e:
            await self.log_message("Ошибка обработки сообщения", error=str(e))


lock_response_consumer = LockResponseKafkaConsumerService(
    settings.LOCK_ASSETS_RESPONSE_TOPIC, settings.BOOTSTRAP_SERVERS, group_id="lock_assets_group"
)
