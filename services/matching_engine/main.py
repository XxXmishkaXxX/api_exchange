import asyncio
import logging
from kafka.consumer import KafkaConsumerService
from kafka.producers import KafkaOrderProducer, KafkaWalletProducer, KafkaMarketDataProducer
from engine.matching_engine import MatchingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        prod_order = KafkaOrderProducer()
        await prod_order.start()
        prod_wallet = KafkaWalletProducer()
        await prod_wallet.start()
        prod_market_data = KafkaMarketDataProducer()
        await prod_market_data.start()

        engine = MatchingEngine(prod_order, prod_wallet, prod_market_data)
        
        consumer_service = KafkaConsumerService(engine)
        await consumer_service.start()
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
