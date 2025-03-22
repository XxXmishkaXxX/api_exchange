import json
from aiokafka import AIOKafkaProducer

class KafkaProducerService:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")

    async def start(self):
        await self.producer.start()

    async def send_order_update(self, order_id, status):
        message = json.dumps({"order_id": order_id, "status": status}).encode("utf-8")
        await self.producer.send("orders_update", message)

    async def stop(self):
        await self.producer.stop()

async def get_producer():
    producer = KafkaProducerService()
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop() 
