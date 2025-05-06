import json
from uuid import UUID

from app.core.config import settings
from app.db.database import get_db
from app.repositories.market_data import MarketDataRepository
from app.models.transaction import Transaction
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class TransactionsConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для получение транзаций.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        
        order_asset_id = int(data.get("order_asset_id"))
        payment_asset_id = int(data.get("payment_asset_id"))
        from_user_id = UUID(data.get("from_user_id"))
        to_user_id = UUID(data.get("to_user_id"))
        price = int(data.get("price"))
        amount = int(data.get("amount"))

        transaction = Transaction(
            order_asset_id=order_asset_id,
            payment_asset_id=payment_asset_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            price=price,
            amount=amount
        )

        await self.add_transaction(transaction=transaction)
    
    async def add_transaction(self, transaction: Transaction):

        async with get_db() as session:
            repo = MarketDataRepository(session=session)
            await repo.add_transaction(transaction)
            await self.log_message("Транзакция добавлена", **transaction.__dict__)


transaction_consumer = TransactionsConsumer(topic=settings.TRANSACTIONS_TOPIC,
                                            bootstrap_servers=settings.BOOTSTRAP_SERVERS, 
                                            group_id="md_transactions")