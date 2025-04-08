import json
import logging
from aiokafka import AIOKafkaConsumer
from engine.matching_engine import MatchingEngine
from engine.order import Order

logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self, engine, kafka_broker="kafka:9092", topic="orders"):
        self.kafka_broker = kafka_broker
        self.topic = topic
        self.consumer = AIOKafkaConsumer(self.topic, bootstrap_servers=self.kafka_broker)
        self.engine = engine

    async def start(self):
        await self.consumer.start()
        logger.info("🚀 Kafka Consumer started")

        try:
            async for msg in self.consumer:
                await self.process_message(msg)
        except Exception as e:
            logger.error(f"❌ Error consuming message: {e}")
        finally:
            await self.stop()

    async def process_message(self, msg):
        """ Обрабатывает входящие ордера из Kafka """
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
                    await self.engine.execute_market_order(order)
                else:
                    self.engine.add_order(order)

            else:
                self.engine.cancel_order(data["order_id"],
                                        data["direction"],
                                        data["ticker"],
                                        data["payment_ticker"])

        except Exception as e:
            logger.error(f"⚠️ Error processing order: {e}")


    async def stop(self):
        await self.consumer.stop()
        logger.info("🔻 Kafka Consumer stopped")
