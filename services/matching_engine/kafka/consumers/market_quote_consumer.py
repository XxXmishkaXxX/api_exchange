import json
from aiokafka import AIOKafkaConsumer
from engine.order import Order
from core.config import settings
from core.logger import logger
from consumers.base_consumer import BaseKafkaConsumer

class MarketQuoteRequestConsumer(BaseKafkaConsumer):
    def __init__(self, engine, bootstrap_servers: str, topic: str,  group_id: str):
        super().__init__(topic, bootstrap_servers=bootstrap_servers, group_id=group_id)
        self.engine = engine

    async def process_message(self, msg):
        try:
            data = json.loads(msg.value.decode("utf-8"))
            logger.info(f"📨 Market quote request received: {data}")

            self.engine.handle_market_quote_request(data["correlation_id"],
                                                        data["order_ticker"], 
                                                        data["payment_ticker"], 
                                                        data["direction"],
                                                        data["amount"])

        except Exception as e:
            logger.error(f"⚠️ Error processing market quote request: {e}")
