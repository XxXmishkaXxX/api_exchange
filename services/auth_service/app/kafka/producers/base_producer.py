from aiokafka import AIOKafkaProducer

from app.core.logger import logger


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