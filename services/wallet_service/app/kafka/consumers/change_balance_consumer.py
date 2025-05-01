import json

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db
from app.deps.fabric import get_wallet_service 
from app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class ChangeBalanceConsumer(BaseKafkaConsumerService):

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)


    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        from_user_raw = data.get("from_user")
        from_user = from_user_raw if from_user_raw is not None else None
        to_user = data.get("to_user")
        ticker = data.get("ticker")
        amount = int(data.get("amount", 0))

        logger.info(f"➡️ Обработка перевода: {data}")

        try:
            async for session in get_db():
                service = await get_wallet_service(session)
                
                asset_id = await service.asset_repo.get_asset_by_ticker(ticker)
                if from_user:
                    from_user_asset = await service.wallet_repo.get(from_user, asset_id)

                    await service.wallet_repo.unlock(from_user_asset, amount)

                    await service.withdraw_assets_user(WithdrawAssetsSchema(user_id=from_user, 
                                                                            ticker=ticker,
                                                                            amount=amount))
                    await service.deposit_assets_user(DepositAssetsSchema(user_id=to_user, 
                                                                        ticker=ticker,
                                                                        amount=amount))
                else:
                    to_user_asset = await service.wallet_repo.get(to_user, asset_id)
                    await service.wallet_repo.unlock(to_user_asset, amount)
                logger.info("✅ Перевод завершён")
                break
        except Exception as e:
            logger.error(f"❌ Ошибка при переводе: {e}")


change_balance_consumer = ChangeBalanceConsumer(topic=settings.POST_TRADE_PROCESSING_TOPIC,
                                                bootstrap_servers=settings.BOOTSTRAP_SERVERS,
                                                group_id="change_balance_wallet")