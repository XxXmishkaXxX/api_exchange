import asyncio
import logging
from kafka.consumer import KafkaConsumerService
from kafka.producer import KafkaProducerService
from engine.matching_engine import MatchingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        producer = KafkaProducerService()
        await producer.start()

        engine = MatchingEngine(producer)
        
        consumer_service = KafkaConsumerService(engine)
        await consumer_service.start()
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
