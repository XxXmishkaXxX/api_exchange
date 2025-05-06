import json

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db
from app.repositories.wallet_repo import WalletRepository
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class ChangeBalanceConsumer(BaseKafkaConsumerService):

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)


    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        from_user_raw = data.get("from_user")
        from_user = from_user_raw if from_user_raw is not None else None
        to_user = data.get("to_user")
        asset_id = data.get("asset_id")
        amount = int(data.get("amount", 0))

        logger.info(f"➡️ Обработка перевода: {data}")

        try:
            async with get_db() as session:
                repo = WalletRepository(session)
                if from_user:
                    await repo.unlock(from_user, asset_id, amount)

                    await repo.withdraw(user_id=from_user, asset_id=asset_id, amount=amount)
                    await repo.deposit(user_id=to_user, asset_id=asset_id, amount=amount)
                else:
                    await repo.unlock(to_user, asset_id, amount)
                logger.info("✅ Перевод завершён")
        except Exception as e:
            logger.error(f"❌ Ошибка при переводе: {e}")


change_balance_consumer = ChangeBalanceConsumer(topic=settings.POST_TRADE_PROCESSING_TOPIC,
                                                bootstrap_servers=settings.BOOTSTRAP_SERVERS,
                                                group_id="change_balance_wallet")