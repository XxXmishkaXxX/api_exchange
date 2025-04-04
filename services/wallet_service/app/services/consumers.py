import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.models.asset import Asset
from app.repositories.asset_repo import AssetRepository 


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


# class ChangeAssetsConsumer(BaseKafkaConsumerService):

#     def __init__(self, topic: str, bootstrap_servers: str):
#         super().__init__(topic, bootstrap_servers)


#     async def process_message(self, message):
#         pass


# class LockAssetsConsumer(BaseKafkaConsumerService):

#     def __init__(self, topic: str, bootstrap_servers: str,):
#         super().__init__(topic, bootstrap_servers)


#     async def process_message(self, message):
#         pass


class AssetConsumer(BaseKafkaConsumerService):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        """Обрабатываем сообщение о добавлении или удалении тикера."""
        try:
            data = self._parse_message(message)
            if not data:
                return

            action = data.get("action")
            asset_id = int(data.get("asset_id"))
            ticker = data.get("ticker")
            name = data.get("name")

            if action == "ADD":
                await self._handle_add_ticker(asset_id, ticker, name)
            elif action == "REMOVE":
                await self._handle_remove_ticker(ticker)
            else:
                logger.warning(f"Неизвестное действие {action} для актива {asset_id}")

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")

    def _parse_message(self, message):
        """Парсим сообщение и возвращаем данные."""
        try:
            return json.loads(message.value.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге сообщения: {str(e)}")
            return None

    async def _handle_add_ticker(self, asset_id: int, ticker: str, name: str):
        """Обрабатываем добавление тикера."""
        if asset_id and ticker and name:
            await self._add_ticker_to_db_and_redis(asset_id, ticker, name)
        else:
            logger.warning(f"Недостаточно данных для добавления тикера: {asset_id}, {ticker}, {name}")

    async def _add_ticker_to_db_and_redis(self, asset_id: int, ticker: str, name: str):
        """Добавляем тикер в базу данных и Redis."""
        asset = Asset(id=asset_id, name=name, ticker=ticker)

        async for session in get_db():
            repo = AssetRepository(session)
            await repo.create(asset)

        
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.hset(asset_key, mapping={"asset_id": asset_id, "name": name})

        logger.info(f"Добавлен актив {asset.id} в базу данных и Redis")

    async def _handle_remove_ticker(self, ticker: str):
        """Обрабатываем удаление тикера."""
        if ticker:
            await self._remove_ticker_from_db_and_redis(ticker)
        else:
            logger.warning(f"Недостаточно данных для удаления актива: {ticker}")

    async def _remove_ticker_from_db_and_redis(self, ticker: str):
        """Удаляем тикер из базы данных и Redis.""" 
        async for session in get_db():
            repo = AssetRepository(session)
            await repo.delete(ticker)

        redis = await redis_pool.get_redis_connection()
        asset_key = f"asset:{ticker}"
        await redis.delete(asset_key)

        logger.info(f"Удалён актив {ticker} из базы данных и Redis")

# Инициализируем с группой потребителей
assets_consumer = AssetConsumer(topic="tickers", bootstrap_servers=settings.BOOTSTRAP_SERVERS, group_id="assets_group")
