from aiokafka import AIOKafkaConsumer

from app.core.logger import logger


class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.

    Этот класс реализует основные функции для подключения, остановки и обработки сообщений из Kafka.
    Классы-наследники должны реализовывать метод process_message для обработки сообщений.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        """
        Инициализация потребителя Kafka.

        Аргументы:
            topic (str): Название Kafka топика.
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers, group_id=group_id)

    async def start(self):
        """Запускает потребителя Kafka."""
        await self.consumer.start()

    async def stop(self):
        """Останавливает потребителя Kafka."""
        await self.consumer.stop()

    async def consume_messages(self):
        """
        Метод для асинхронного потребления сообщений из Kafka.

        Ожидает новые сообщения и передает их на обработку.
        """
        async for message in self.consumer:
            await self.process_message(message)

    async def process_message(self, message):
        """
        Метод для обработки сообщения.

        Должен быть реализован в наследниках.

        Аргументы:
            message: Сообщение, полученное от Kafka.
        """
        raise NotImplementedError("Метод process_message должен быть реализован в наследниках")

    async def log_message(self, action: str, **kwargs):
        """
        Логирует информацию о сообщении.
        """
        logger.info(f"{action}: {kwargs}")
