import json
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings
from app.core.logger import logger

from aiokafka import AIOKafkaProducer
import json
import logging

logger = logging.getLogger(__name__)

class BaseKafkaProducerService:
    """
    Сервис для взаимодействия с Kafka, отправляющий сообщения о заказах.
    """

    def __init__(self, topic: str, bootstrap_servers: str):
        """
        Инициализация Kafka продюсера.

        Аргументы:
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self) -> None:
        """Запуск продюсера Kafka."""
        await self.producer.start()

    async def stop(self) -> None:
        """Остановка продюсера Kafka."""
        await self.producer.stop()

    async def send_message(self, message: bytes):
        """
        Метод для отправки сообщения в Kafka.

        Аргументы:
            message (bytes): Сообщение для отправки в Kafka.
        """
        try:
            await self.producer.send_and_wait(self.topic, message)
            logger.info(f"Message sent to Kafka topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")


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




lock_uab_resp_producer = LockUserAssetBalanceResponseProducer(topic="lock_assets.response",
                                                            bootstrap_servers=settings.BOOTSTRAP_SERVERS)



async def get_lock_uab_resp_producer_service() -> AsyncGenerator[LockUserAssetBalanceResponseProducer, None]:
    """
    Асинхронный генератор для получения экземпляра сервиса Kafka продюсера.

    Возвращает:
        ChangeBalanceKafkaProducerService: Экземпляр сервиса Kafka продюсера.
    """
    yield lock_uab_resp_producer
