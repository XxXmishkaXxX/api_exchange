import asyncio
import logging
from kafka.consumer import KafkaConsumerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        consumer_service = KafkaConsumerService()
        await consumer_service.start()
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
