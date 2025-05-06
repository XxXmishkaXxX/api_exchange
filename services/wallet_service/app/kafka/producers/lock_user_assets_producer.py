import json

from app.core.config import settings
from app.core.logger import logger
from app.kafka.producers.base_producer import BaseKafkaProducerService


class LockUserAssetBalanceResponseProducer(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        """
        Класс для отправки сообщений в тему Kafka с ответом на запрос о блокировке активов.

        Аргументы:
            topic (str): Тема Kafka для отправки ответа.
            bootstrap_servers (str): Список адресов Kafka серверов.
        """
        super().__init__(topic, bootstrap_servers)

    async def send_response(self, correlation_id: str, success: bool):
        """
        Отправка ответа о результатах блокировки активов.

        Аргументы:
            correlation_id (str): Идентификатор запроса для связывания с исходным сообщением.
            success (bool): Успешность операции (True/False).
        """
        response_data = {
            "correlation_id": correlation_id,
            "success": success
        }

        message = json.dumps(response_data)

        await self.send_message(message.encode("utf-8"))
        logger.info(f"Sent lock response: correlation_id={correlation_id}, success={success}")




lock_uab_resp_producer = LockUserAssetBalanceResponseProducer(topic=settings.LOCK_ASSETS_RESPONSE_TOPIC,
                                                            bootstrap_servers=settings.BOOTSTRAP_SERVERS)

