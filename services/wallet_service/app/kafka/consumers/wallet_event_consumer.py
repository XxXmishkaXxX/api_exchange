import json
from uuid import UUID

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db
from app.repositories.wallet_repo import WalletRepository
from app.kafka.consumers.base_consumer import BaseKafkaConsumerService


class WalletEventsConsumerService(BaseKafkaConsumerService):

    def __init__(self, topic: str, bootstrap_server: str, group_id: str):
        super().__init__(topic=topic, bootstrap_servers=bootstrap_server, group_id=group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        user_id = UUID(data.get("user_id"))
        event = data.get("event")

        logger.info(f"{event} wallet for user_id={user_id}")
        async with get_db() as session:
            repo = WalletRepository(session)
            try:
                if event == "create":
                    await repo.create(user_id=user_id)
                else:
                    await repo.delete_all_assets_user(user_id=user_id)
            except Exception as e:
                logger.error(e)
                raise e


wallet_event_consumer = WalletEventsConsumerService(topic=settings.WALLET_EVENTS_TOPIC,
                                                    bootstrap_server=settings.BOOTSTRAP_SERVERS,
                                                    group_id="wallet_events_group")