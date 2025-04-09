import json
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.logger import logger
from app.db.database import get_db, redis_pool
from app.models.asset import Asset
from app.repositories.asset_repo import AssetRepository
from app.repositories.wallet_repo import WalletRepository
from app.deps.fabric import get_wallet_service 
from app.schemas.wallet import DepositAssetsSchema, WithdrawAssetsSchema
from app.services.producers import get_lock_uab_resp_producer_service


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

        from_user_raw = data.get("from_user")
        from_user = int(from_user_raw) if from_user_raw is not None else None
        to_user = int(data.get("to_user"))
        ticker = data.get("ticker")
        amount = int(data.get("amount", 0))

        logger.info(f"➡️ Обработка перевода: {data}")

        try:
            async for session in get_db():
                service = await get_wallet_service(session)
                
                asset_id = await service.asset_repo.get_asset_by_ticker(ticker)
                if from_user:
                    from_user_asset = await service.wallet_repo.get(from_user, asset_id)

                    logger.info(f"Блокировка активов до перевода: {from_user_asset.locked}")
                    await service.wallet_repo.unlock(from_user_asset, amount)
                    logger.info(f"Блокировка активов после перевода: {from_user_asset.locked}")

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


class LockAssetsConsumer(BaseKafkaConsumerService):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str):
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
            async for producer in get_lock_uab_resp_producer_service(): 
                await producer.send_response(correlation_id, success)
                break

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

            # Проверка доступных средств для блокировки
            available = user_asset.amount - user_asset.locked
            if available >= lock_amount:
                # Если доступных средств хватает, то блокируем
                await repo.lock(user_asset, lock_amount)
                logger.info(f"Assets locked for user {user_id}, asset {ticker}, amount {lock_amount}")
                return True
            else:
                logger.warning(f"Insufficient funds to lock for user {user_id}, asset {ticker}, required {lock_amount}, available {available}")
                return False

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