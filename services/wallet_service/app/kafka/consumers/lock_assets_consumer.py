import json

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db
from app.repositories.wallet_repo import WalletRepository
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService
from app.kafka.producers.lock_user_assets_producer import lock_uab_resp_producer, LockUserAssetBalanceResponseProducer


class LockAssetsConsumer(BaseKafkaConsumerService):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, prod: LockUserAssetBalanceResponseProducer):
        self.prod = prod
        super().__init__(topic, bootstrap_servers, group_id)
        

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        correlation_id = data.get("correlation_id")
        user_id = data.get("user_id")
        asset_id = data.get("asset_id")
        ticker = data.get("ticker")
        lock = int(data.get("amount"))

        logger.info(f"Received lock request: user={user_id}, asset={ticker}, amount={lock}, correlation_id={correlation_id}")

        try:
            success = await self.handle_assets(user_id, asset_id, ticker, lock)
        except Exception as e:
            logger.exception(f"Error handling lock for user {user_id}, asset {ticker}: {e}")
            success = False

        if correlation_id:
            await self.prod.send_response(correlation_id, success)

    async def handle_assets(self, user_id: str, asset_id: int, ticker: str, lock_amount: int) -> bool:
        """
        Обрабатывает блокировку активов для пользователя.

        Аргументы:
            user_id (str): Идентификатор пользователя.
            asset_id (int): Идентификатор актива.
            ticker (str): Тикер актива.
            lock_amount (int): Количество средств для блокировки.

        Возвращает:
            bool: Успешность операции блокировки.
        """
        async for session in get_db():
            repo = WalletRepository(session)
            user_asset = await repo.get(user_id, asset_id)

            if not user_asset:
                logger.warning(f"User asset not found for user {user_id}, asset {ticker}")
                return False

            available = user_asset.amount - user_asset.locked
            if available >= lock_amount:
                await repo.lock(user_asset, lock_amount)
                logger.info(f"Assets locked for user {user_id}, asset {ticker}, amount {lock_amount}")
                return True
            else:
                logger.warning(f"Insufficient funds to lock for user {user_id}, asset {ticker}, required {lock_amount}, available {available}")
                return False
            

lock_asset_amount_consumer = LockAssetsConsumer(topic=settings.LOCK_ASSETS_REQUEST_TOPIC, 
                                                bootstrap_servers=settings.BOOTSTRAP_SERVERS, 
                                                group_id="lock_assets_wallet",
                                                prod=lock_uab_resp_producer)