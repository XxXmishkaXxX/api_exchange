import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.models.asset import Asset
from app.repositories.asset_repo import AssetRepository
from app.repositories.wallet_repo import WalletRepository
from app.services.wallet import get_wallet_service


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

    async def log_message(self, action: str, **kwargs):
        """
        Логирует информацию о сообщении.
        """
        logger.info(f"{action}: {kwargs}")


class ChangeBalanceConsumer(BaseKafkaConsumerService):

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)


    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        from_user = int(data.get("from_user"))
        to_user = int(data.get("to_user"))
        asset_id = data.get("asset_id")
        amount = int(data.get("amount", 0))

        logger.info(f"➡️ Обработка перевода: {data}")

        try:
            async for session in get_db():
                repo = WalletRepository(session)
                from_user_asset = await repo.get(from_user, asset_id)
                to_user_asset = await repo.get(to_user, asset_id)

                await repo.unlock(from_user_asset, amount)
                await repo.withdraw(from_user_asset, amount)
                if to_user_asset is None:
                    await repo.create(to_user, asset_id, amount)
                else:
                    await repo.deposit(to_user_asset, amount)
                logger.info("✅ Перевод завершён")
                break
        except Exception as e:
            logger.error(f"❌ Ошибка при переводе: {e}")


class LockAssetsConsumer(BaseKafkaConsumerService):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))

        action = data.get("action")
        user_id = data.get("user_id")
        asset_id = data.get("asset_id")
        ticker = data.get("ticker")
        amount = int(data.get("amount"))

        if action == "lock":
            await self.handle_assets(user_id, asset_id, ticker, amount, lock=True)
        elif action == "unlock":
            await self.handle_assets(user_id, asset_id, ticker, amount, lock=False)

    async def handle_assets(self, user_id: str, asset_id: int, ticker: str, amount: int, lock: bool):
        async for session in get_db():
            repo = WalletRepository(session)
            user_asset = await repo.get(user_id, asset_id)

            if not user_asset:
                logger.warning(f"User asset not found for user {user_id}, asset {ticker}")
                return

            current_amount = user_asset.amount
            locked_amount = user_asset.locked

            if lock:
                if current_amount - locked_amount >= amount:
                    await repo.lock(user_asset, amount)

                    logger.info(f"Assets locked for user {user_id}, asset {ticker}, amount {amount}")
                else:
                    await self._fallback_lock(user_id, asset_id, ticker, amount, repo)
            else:
                if locked_amount >= amount:
                    await repo.unlock(user_asset, amount)

                    logger.info(f"Assets unlocked for user {user_id}, asset {ticker}, amount {amount}")
                else:
                    await self._fallback_unlock(user_id, asset_id, ticker, amount, repo)

    async def _fallback_lock(self, user_id: str, asset_id: int, ticker: str, amount: int, repo: WalletRepository):
        user_asset = await repo.get(user_id, asset_id)

        if user_asset and (user_asset.amount - user_asset.locked) >= amount:
            await repo.lock(user_asset, amount)

            logger.info(f"Assets locked (fallback) for user {user_id}, asset {ticker}, amount {amount}")
        else:
            logger.warning(f"Insufficient funds to lock (fallback) for user {user_id}, asset {ticker}, amount {amount}")

    async def _fallback_unlock(self, user_id: str, asset_id: int, ticker: str, amount: int, repo: WalletRepository):
        user_asset = await repo.get(user_id, asset_id)

        if user_asset and user_asset.locked >= amount:
            await repo.unlock(user_asset, amount)

            logger.info(f"Assets unlocked (fallback) for user {user_id}, asset {ticker}, amount {amount}")
        else:
            logger.warning(f"Failed to unlock assets (fallback) for user {user_id}, asset {ticker}, amount {amount}: Insufficient locked funds")


class AssetConsumer(BaseKafkaConsumerService):
    """
    Потребитель Kafka для обработки тикеров.
    """

    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
        super().__init__(topic, bootstrap_servers, group_id)

    async def process_message(self, message):
        data = json.loads(message.value.decode("utf-8"))
        action = data.get("action")
        asset_id = data.get("asset_id")
        ticker = data.get("ticker")
        name = data.get("name")

        if action == "ADD" and asset_id and ticker and name:
            await self.add_asset_to_redis_and_db(asset_id, ticker, name)
        elif action == "REMOVE" and ticker:
            await self.remove_asset_from_redis_and_db(ticker)

    async def add_asset_to_redis_and_db(self, asset_id: int, ticker: str, name: str):
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.hset(asset_key, mapping={"asset_id": asset_id, "name": name})
            await self.log_message("Добавлен актив в Redis", ticker=ticker, name=name)

        async for session in get_db():
            repo = AssetRepository(session)
            asset = Asset(id=asset_id, name=name, ticker=ticker)
            await repo.create(asset)
            await self.log_message("Добавлен актив в DB", ticker=ticker, name=name)

    async def remove_asset_from_redis_and_db(self, ticker: str):
        async with redis_pool.connection() as redis:
            asset_key = f"asset:{ticker}"
            await redis.delete(asset_key)
            await self.log_message("Удалён актив из Redis", ticker=ticker)

        async for session in get_db():
            repo = AssetRepository(session)
            await repo.delete(ticker)
            await self.log_message("Удалён актив из DB", ticker=ticker)



change_balance_consumer = ChangeBalanceConsumer(topic="post_trade_processing", bootstrap_servers=settings.BOOTSTRAP_SERVERS, group_id=None)
assets_consumer = AssetConsumer(topic="tickers", bootstrap_servers=settings.BOOTSTRAP_SERVERS, group_id="assets_group")
lock_asset_amount_consumer = LockAssetsConsumer(topic="lock_assets", bootstrap_servers=settings.BOOTSTRAP_SERVERS, group_id=None)