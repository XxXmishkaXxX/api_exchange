import json
from uuid import UUID
from datetime import datetime, timezone

from app.core.config import settings
from app.db.database import get_db
from app.repositories.market_data import MarketDataRepository
from app.repositories.asset_repo import AssetRepository
from app.models.transaction import Transaction
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class TransactionsConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для получения транзакций.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        order_asset_ticker = data.get("order_ticker")
        payment_asset_ticker = data.get("payment_ticker")
        from_user_id = UUID(data.get("from_user_id"))
        to_user_id = UUID(data.get("to_user_id"))
        price = int(data.get("price"))
        amount = int(data.get("amount"))

        await self.add_transaction(
            order_asset_ticker=order_asset_ticker,
            payment_asset_ticker=payment_asset_ticker,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            price=price,
            amount=amount,
        )
    
    async def add_transaction(
        self,
        order_asset_ticker: str,
        payment_asset_ticker: str,
        from_user_id: UUID,
        to_user_id: UUID,
        price: int,
        amount: int,
    ):
        async with get_db() as session:
            asset_repo = AssetRepository(session=session)
            order_asset = await asset_repo.get_asset_by_ticker(order_asset_ticker)
            payment_asset = await asset_repo.get_asset_by_ticker(payment_asset_ticker)

            transaction = Transaction(
                order_asset_id=order_asset.id,
                payment_asset_id=payment_asset.id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                price=price,
                amount=amount
            )
            repo = MarketDataRepository(session=session)
            await repo.add_transaction(transaction)


transaction_consumer = TransactionsConsumer(
    topic=settings.TRANSACTIONS_TOPIC,
    bootstrap_servers=settings.BOOTSTRAP_SERVERS,
    group_id="md_transactions"
)
