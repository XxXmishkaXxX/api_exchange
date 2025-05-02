from aiokafka import AIOKafkaConsumer

from core.logger import logger


class BaseKafkaConsumer:
    def __init__(self, topic, bootstrap_servers, group_id=None):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = AIOKafkaConsumer(self.topic, 
                                        bootstrap_servers=self.bootstrap_servers,
                                        group_id=group_id,
                                        auto_offset_reset="latest",
                                        enable_auto_commit=True)

    async def start(self):
        await self.consumer.start()
        logger.info(f"🚀 Kafka Consumer started for topic: {self.topic}")

        try:
            async for msg in self.consumer:
                await self.process_message(msg)
        except Exception as e:
            logger.error(f"❌ Error consuming message from {self.topic}: {e}")
        finally:
            await self.stop()

    async def stop(self):
        await self.consumer.stop()
        logger.info(f"🔻 Kafka Consumer stopped for topic: {self.topic}")

    async def process_message(self, msg):
        """To be implemented by subclasses"""
        raise NotImplementedError("process_message must be implemented by subclasses")