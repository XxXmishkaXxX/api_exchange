import asyncio
import os

from core.loggers.system_logger import logger
from kafka.consumers.market_quote_consumer import MarketQuoteRequestConsumer
from kafka.consumers.order_consumer import OrderConsumerService
from kafka.producers import (
    KafkaOrderProducer,
    KafkaWalletProducer,
    KafkaMarketQuoteResponseProducer,
    KafkaSendTransactionProducer,
)
from redis_client.redis_client import RedisOrderClient
from messaging.producer_service import ProducerService
from core.config import settings
from engine.matching_engine import MatchingEngine
from recovery.snapshots_manager.manager import SnapshotManager
from recovery.order_logs_replayer.logs_replayer import OrderLogReplayer

SNAPSHOTS_PATH = "snapshots/orderbooks_snapshot.json"
LOGS_PATH = "logs/orders.log"

async def create_kafka_producers():
    """Создаёт и запускает все Kafka продюсеры."""
    producers = [
        KafkaOrderProducer(),
        KafkaWalletProducer(),
        KafkaMarketQuoteResponseProducer(),
        KafkaSendTransactionProducer(),
    ]
    try:
        await asyncio.gather(*(producer.start() for producer in producers))
        logger.info("✅ Kafka producers started successfully.")
    except Exception as e:
        logger.error(f"❌ Error starting Kafka producers: {e}")
        raise
    return producers

def create_redis_client():
    """Создаёт синхронное подключение к Redis."""
    redis_client = RedisOrderClient(settings.REDIS_URL)
    try:
        redis_client.redis_client.ping()
        logger.info("✅ Подключение к Redis установлено.")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Redis: {e}")
        raise
    return redis_client

def create_matching_engine(order_books: dict, redis_client, messaging_service: ProducerService) -> MatchingEngine:
    """Создаёт экземпляр MatchingEngine."""
    try:
        engine = MatchingEngine(order_books, messaging_service, redis_client)
        logger.info("✅ Matching engine создан.")
        return engine
    except Exception as e:
        logger.error(f"❌ Error creating MatchingEngine: {e}")
        raise

async def start_consumer_services(engine: MatchingEngine):
    """Запускает сервисы Kafka consumers."""
    try:
        order_consumer = OrderConsumerService(
            engine,
            topic=settings.ORDERS_TOPIC,
            bootstrap_servers=settings.BOOTSTRAP_SERVERS,
            group_id="orders_engine",
        )
        market_quote_consumer = MarketQuoteRequestConsumer(
            engine,
            topic=settings.MARKET_QUOTE_REQUEST_TOPIC,
            bootstrap_servers=settings.BOOTSTRAP_SERVERS,
            group_id="market_quote_engine",
        )

        await asyncio.gather(
            order_consumer.start(),
            market_quote_consumer.start()
        )
        logger.info("✅ Kafka consumers запущены.")
    except Exception as e:
        logger.error(f"❌ Error starting Kafka consumers: {e}")
        raise

async def periodic_snapshot(snapshot_manager: SnapshotManager, interval: int = 600):
    """Периодически сохраняет снапшоты ордербуков."""
    try:
        while True:
            snapshot_manager.save_snapshot()
            logger.info("✅ Snapshot saved.")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.warning("⏹️ Snapshot saving cancelled.")
    except Exception as e:
        logger.error(f"❌ Error during snapshot saving: {e}")
        raise

async def main():
    """Основной процесс приложения."""
    try:
        kafka_producers = await create_kafka_producers()
        prod_order, prod_wallet, prod_market_quote, prod_transaction = kafka_producers

        redis_client = create_redis_client()

        messaging_service = ProducerService(prod_order, prod_wallet, prod_market_quote, prod_transaction)

        snapshot_manager = SnapshotManager({}, SNAPSHOTS_PATH)
        order_books, snapshot_timestamp = snapshot_manager.load_snapshot()
        logger.info("📦 Snapshot loaded at timestamp: %s", snapshot_timestamp)

        if os.path.exists(LOGS_PATH) and order_books:
            replayer = OrderLogReplayer(LOGS_PATH, snapshot_timestamp)
            replayer.truncate_before_snapshot()
            replayer.replay(order_books)
            logger.info("✅ Order log replayed successfully after snapshot recovery.")
        elif not order_books:
            logger.warning("⚠️ No snapshot found, starting with empty orderbooks")
        else:
            logger.warning("⚠️ No order log found, starting only from snapshot.")

        engine = create_matching_engine(order_books, redis_client, messaging_service)
        snapshot_manager.books = engine.order_books

        await asyncio.gather(
            start_consumer_services(engine),
            periodic_snapshot(snapshot_manager),
        )

    except Exception as e:
        logger.error(f"❌ Application error: {e}")
    finally:
        logger.info("🚀 Shutting down application...")

if __name__ == "__main__":
    asyncio.run(main())
