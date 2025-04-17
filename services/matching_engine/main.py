import asyncio
import logging
from kafka.consumer import OrderConsumerService, MarketQuoteRequestConsumer
from kafka.producers import KafkaOrderProducer, KafkaWalletProducer, KafkaMarketDataProducer, KafkaMarketQuoteResponseProducer
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
        prod_market_quote = KafkaMarketQuoteResponseProducer()
        await prod_market_quote.start()
        return prod_order, prod_wallet, prod_market_data, prod_market_quote
    except Exception as e:
        logger.error(f"❌ Error starting Kafka producers: {e}")
        raise

async def create_matching_engine(prod_order, prod_wallet, prod_market_data, prod_market_quote):
    """Создаёт экземпляр MatchingEngine."""
    try:
        return MatchingEngine(prod_order, prod_wallet, prod_market_data, prod_market_quote)
    except Exception as e:
        logger.error(f"❌ Error creating MatchingEngine: {e}")
        raise

async def start_consumers_services(engine):
    """Запускает Kafka consumer service в отдельных задачах."""
    try:
        order_consumer_service = OrderConsumerService(engine)
        market_quote_request_consumer_service = MarketQuoteRequestConsumer(engine)

        # Создаём задачи
        order_task = asyncio.create_task(order_consumer_service.start())
        quote_task = asyncio.create_task(market_quote_request_consumer_service.start())

        logger.info("✅ Kafka consumers запущены.")

        await asyncio.gather(order_task, quote_task)
    except Exception as e:
        logger.error(f"❌ Error starting KafkaConsumerService: {e}")
        raise

async def main():
    """Основной асинхронный процесс приложения."""
    try:
        prod_order, prod_wallet, prod_market_data, prod_market_quote = await create_producers()
        engine = await create_matching_engine(prod_order, prod_wallet, prod_market_data, prod_market_quote)
        await start_consumers_services(engine)
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
