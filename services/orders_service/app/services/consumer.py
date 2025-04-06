import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.repositories.order_repo import OrderRepository
from app.services.wallet_client import wallet_client


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


class OrderStatusConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки обновлений статуса ордеров.

    Этот класс слушает топик 'orders_update' и обновляет статус ордера в базе данных.
    """

    def __init__(self, bootstrap_servers: str, group_id):
        """
        Инициализация потребителя статусов ордеров.

        Аргументы:
            bootstrap_servers (str): Адреса серверов Kafka.
        """
        super().__init__("orders_update", bootstrap_servers, group_id=group_id)

    async def process_message(self, message):
        """
        Обрабатывает сообщение об обновлении статуса ордера.

        Аргументы:
            message: Сообщение, содержащее информацию о статусе ордера.
        """
        data = json.loads(message.value.decode("utf-8"))
        order_id = int(data["order_id"])
        user_id = int(data["user_id"])
        status = str(data["status"])
        await self.change_order_status(order_id, user_id, status)

    async def change_order_status(self, order_id: int, user_id: int, status: str):
        """
        Изменяет статус ордера в базе данных.

        Аргументы:
            order_id (int): ID ордера.
            user_id (int): ID пользователя.
            status (str): Новый статус ордера.
        """
        async for session in get_db():
            order_repo = OrderRepository(session)
            order = await order_repo.get(order_id, user_id)
            if order:
                await order_repo.update(order, {"status": status})


class AssetConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки тикеров.

    Этот класс слушает топик 'tickers' и обновляет данные о тикерах в Redis.
    """

    def __init__(self, bootstrap_servers: str, group_id: str):
        """
        Инициализация потребителя тикеров.

        Аргументы:
            bootstrap_servers (str): Адреса серверов Kafka.
            group_id (str): ID группы потребителей.
        """
        super().__init__("tickers", bootstrap_servers, group_id=group_id)


    async def process_message(self, message):
        """
        Обрабатывает сообщение о тикере.

        Аргументы:
            message: Сообщение, содержащее информацию о тикере.
        """
        data = json.loads(message.value.decode("utf-8"))
        action = data.get("action")
        ticker_id = data.get("asset_id")
        symbol = data.get("ticker")
        name = data.get("name")

        if action == "ADD" and ticker_id and symbol and name:
            async with redis_pool.connection() as redis:
                ticker_key = f"ticker:{ticker_id}"
                await redis.hset(ticker_key, mapping={"symbol": symbol, "name": name})
                logger.info(f"Добавлен тикер в Redis: {ticker_id} -> {symbol} ({name})")

        elif action == "REMOVE" and ticker_id:
            async with redis_pool.connection() as redis:
                ticker_key = f"ticker:{ticker_id}"
                await redis.delete(ticker_key)
                logger.info(f"Удалён тикер из Redis: {ticker_id}")


class ChangeBalanceConsumer(BaseKafkaConsumerService):

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic=topic, bootstrap_servers=bootstrap_servers,
                         group_id=group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode('utf-8'))

        user_id = data["user_id"]
        asset = data["asset"]
        amount = int(data["amount"])
        lock = int(data["lock"])

        balance_key = f"user:{user_id}:asset:{asset}"

        async with redis_pool.connection() as redis:
            exists = await redis.exists(balance_key)

            if not exists:
                # Запрос в wallet service
                wallet_data = await wallet_client.get_balance(user_id, asset)
                if wallet_data is None:
                    logger.warning(f"No wallet data found for user={user_id}, asset={asset}")
                    return

                await redis.hset(balance_key, mapping={
                    "amount": int(wallet_data["amount"]),
                    "lock": int(wallet_data["lock"])
                })
                logger.info(f"[INIT] user:{user_id}, asset:{asset}, amount:{wallet_data['amount']}, lock:{wallet_data['lock']}")
            else:
                await redis.hset(balance_key, mapping={
                    "amount": amount,
                    "lock": lock
                })
                logger.info(f"[UPDATE] user:{user_id}, asset:{asset}, amount:{amount}, lock:{lock}")
        

change_balance_consumer = ChangeBalanceConsumer("change_balance", settings.BOOTSTRAP_SERVERS, group_id=None)
order_status_consumer = OrderStatusConsumer(settings.BOOTSTRAP_SERVERS, group_id=None)
asset_consumer = AssetConsumer(settings.BOOTSTRAP_SERVERS, group_id="orders_group")

