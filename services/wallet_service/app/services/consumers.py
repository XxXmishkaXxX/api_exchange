import json
from aiokafka import AIOKafkaConsumer
# from redis import asyncio as aioredis

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db


class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.

    Этот класс реализует основные функции для подключения, остановки и обработки сообщений из Kafka.
    Классы-наследники должны реализовывать метод process_message для обработки сообщений.
    """

    def __init__(self, topic: str, bootstrap_servers: str):
        """
        Инициализация потребителя Kafka.

        Аргументы:
            topic (str): Название Kafka топика.
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.bootstrap_servers)

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


class ChangeAssetsConsumer(BaseKafkaConsumerService):

    def __init__(self, ):
        pass


    async def process_message(self, message):
        pass


class LockAssetsConsumer(BaseKafkaConsumerService):

    def __init__(self, ):
        pass


    async def process_message(self, message):
        pass



change_assets_consumer = ChangeAssetsConsumer()
lock_assets_consumer = LockAssetsConsumer()