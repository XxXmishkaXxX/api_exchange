import asyncio
import logging
from kafka.consumer import KafkaConsumerService
from kafka.producers import KafkaOrderProducer, KafkaWalletProducer, KafkaMarketDataProducer
from engine.matching_engine import MatchingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_producers():
    """Создаёт и запускает все Kafka продюсеры."""
    try:
        prod_order = KafkaOrderProducer()
        await prod_order.start()
        prod_wallet = KafkaWalletProducer()
        await prod_wallet.start()
        prod_market_data = KafkaMarketDataProducer()
        await prod_market_data.start()
        return prod_order, prod_wallet, prod_market_data
    except Exception as e:
        logger.error(f"❌ Error starting Kafka producers: {e}")
        raise

async def create_matching_engine(prod_order, prod_wallet, prod_market_data):
    """Создаёт экземпляр MatchingEngine."""
    try:
        return MatchingEngine(prod_order, prod_wallet, prod_market_data)
    except Exception as e:
        logger.error(f"❌ Error creating MatchingEngine: {e}")
        raise

async def start_consumer_service(engine):
    """Запускает Kafka consumer service."""
    try:
        consumer_service = KafkaConsumerService(engine)
        await consumer_service.start()
    except Exception as e:
        logger.error(f"❌ Error starting KafkaConsumerService: {e}")
        raise

async def main():
    """Основной асинхронный процесс приложения."""
    try:
        prod_order, prod_wallet, prod_market_data = await create_producers()
        engine = await create_matching_engine(prod_order, prod_wallet, prod_market_data)
        await start_consumer_service(engine)
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
