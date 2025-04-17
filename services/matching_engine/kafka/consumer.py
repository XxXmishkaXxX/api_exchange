import json
import logging
from aiokafka import AIOKafkaConsumer
from engine.order import Order

logger = logging.getLogger(__name__)

class BaseKafkaConsumer:
    def __init__(self, topic, kafka_broker="kafka:9092"):
        self.kafka_broker = kafka_broker
        self.topic = topic
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.kafka_broker)

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


class OrderConsumerService(BaseKafkaConsumer):
    def __init__(self, engine, kafka_broker="kafka:9092", topic="orders"):
        super().__init__(topic, kafka_broker)
        self.engine = engine

    async def process_message(self, msg):
        try:
            data = json.loads(msg.value.decode("utf-8"))

            if data["action"] == "add":
                logger.info(f"📩 ORDER RECEIVED: {data}")

                order = Order(
                    order_id=int(data["order_id"]),
                    user_id=int(data["user_id"]),
                    status=data["status"],
                    type=data["type"],
                    direction=data["direction"],
                    order_asset_id=int(data["order_asset_id"]),
                    order_ticker=str(data["order_ticker"]),
                    payment_ticker=str(data["payment_ticker"]),
                    payment_asset_id=int(data["payment_asset_id"]),
                    price=int(data["price"]) if data["price"] is not None else 0,
                    qty=int(data["qty"]),
                    filled=int(data["filled"])
                )

                if order.type == "market":
                    logger.info(f"📈 MARKET ORDER DETECTED: {order}")
                    self.engine.execute_market_order(order)
                else:
                    self.engine.add_order(order)

            else:
                logger.info("CANCEL ORDER")
                self.engine.cancel_order(
                    data["order_id"],
                    data["direction"],
                    data["order_ticker"],
                    data["payment_ticker"]
                )

        except Exception as e:
            logger.error(f"⚠️ Error processing order: {e}")


class MarketQuoteRequestConsumer(BaseKafkaConsumer):
    def __init__(self, engine, kafka_broker="kafka:9092", topic="market_quote.request"):
        super().__init__(topic, kafka_broker)
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
