from aiokafka import AIOKafkaConsumer

from app.core.logger import logger

class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, auto_offset_reset: str = "latest",
                 enable_auto_commit: bool = True):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, 
                                        bootstrap_servers=self.bootstrap_servers, 
                                        group_id=group_id,
                                        auto_offset_reset=auto_offset_reset,
                                        enable_auto_commit=enable_auto_commit)

    async def start(self):
        """Запускает потребителя Kafka."""
        await self.consumer.start()

    async def stop(self):
        """Останавливает потребителя Kafka."""
        await self.consumer.stop()

    async def consume_messages(self):
        """Метод для асинхронного потребления сообщений из Kafka."""
        async for message in self.consumer:
            await self.process_message(message)

    async def process_message(self, message):
        """
        Метод для обработки сообщения. Должен быть реализован в наследниках.
        """
        raise NotImplementedError("Метод process_message должен быть реализован в наследниках")

    async def log_message(self, action: str, **kwargs):
        """
        Логирует информацию о сообщении.
        """
        logger.info(f"{action}: {kwargs}")
