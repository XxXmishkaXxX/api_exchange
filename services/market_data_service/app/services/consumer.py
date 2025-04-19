import json
from aiokafka import AIOKafkaConsumer
from typing import Optional


from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db
from app.repositories.market_data import MarketDataRepository
from app.models.transaction import Transaction


class BaseKafkaConsumerService:
    """
    Базовый класс для потребителей Kafka.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
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


class TransactionsConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для получение транзаций.
    """

    def __init__(self, bootstrap_servers: str, group_id: str):
        super().__init__("transactions", bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        
        order_asset_id = int(data.get("order_asset_id"))
        payment_asset_id = int(data.get("payment_asset_id"))
        from_user_id = int(data.get("from_user_id"))
        to_user_id = int(data.get("to_user_id"))
        price = int(data.get("price"))
        amount = int(data.get("amount"))
        direction = data.get("direction")

        transaction = Transaction(
            order_asset_id=order_asset_id,
            payment_asset_id=payment_asset_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            price=price,
            amount=amount,
            direction=direction
        )

        await self.add_transaction(transaction=transaction)
    
    async def add_transaction(self, transaction: Transaction):

        async for session in get_db():
            repo = MarketDataRepository(session=session)
            await repo.add_transaction(transaction)
            await self.log_message("Транзакция добавлена", **transaction.__dict__)
            break


transaction_consumer = TransactionsConsumer(bootstrap_servers=settings.BOOTSTRAP_SERVERS, group_id=None)