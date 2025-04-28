import json
from uuid import UUID
from aiokafka import AIOKafkaProducer
from typing import AsyncGenerator

from app.core.config import settings
from app.models.order import Order
from app.kafka.producers.base_producer import BaseKafkaProducerService

class MarketQuoteKafkaProducerService(BaseKafkaProducerService):
    def __init__(self, topic: str, bootstrap_servers: str):
        super().__init__(bootstrap_servers=bootstrap_servers, topic=topic)

    async def send_request(self, correlation_id, order_ticker: str, payment_ticker: str, amount: int, direction: str):
        data = {
            "correlation_id": correlation_id,
            "order_ticker": order_ticker,
            "payment_ticker": payment_ticker,
            "amount": amount,
            "direction": direction
        }
        await self.send_message(data)


market_quote_producer = MarketQuoteKafkaProducerService(settings.MARKET_QUOTE_REQUEST_TOPIC,
                                                        bootstrap_servers=settings.BOOTSTRAP_SERVERS)

async def get_market_qoute_producer() -> AsyncGenerator[MarketQuoteKafkaProducerService, None]:
    yield market_quote_producer