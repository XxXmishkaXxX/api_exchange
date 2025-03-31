import json
from aiokafka import AIOKafkaProducer
from app.core.config import settings


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    async def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            self._producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
            await self._producer.start()
        return self._producer

    async def close(self):
        """Остановка продюсера Kafka"""
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def _serialize_message(self, data: dict) -> bytes:
        return json.dumps(data).encode("utf-8")

    async def send_message(self, data: dict):
        producer = await self._get_producer()
        message = await self._serialize_message(data)
        await producer.send_and_wait("tickers", message)
    


producer_service = KafkaProducerService(bootstrap_servers=settings.BOOTSTRAP_SERVERS)


async def get_producer_service():
    yield producer_service
    await producer_service.close()
