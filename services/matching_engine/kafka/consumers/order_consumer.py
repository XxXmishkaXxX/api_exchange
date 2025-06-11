import json
from engine.order import Order
from core.loggers.system_logger import logger
from kafka.consumers.base_consumer import BaseKafkaConsumer


class OrderConsumerService(BaseKafkaConsumer):
    def __init__(self, engine, bootstrap_servers: str, topic: str,  group_id: str):
        super().__init__(topic, bootstrap_servers=bootstrap_servers, group_id=group_id)
        self.engine = engine

    async def process_message(self, msg):
        try:
            data = json.loads(msg.value.decode("utf-8"))

            if data["action"] == "add":
                logger.info(f"📩 ORDER RECEIVED: {data}")

                order = Order(
                    order_id=data["order_id"],
                    user_id=data["user_id"],
                    status=data["status"],
                    direction=data["direction"],
                    order_asset_id=int(data["order_asset_id"]),
                    order_ticker=str(data["order_ticker"]),
                    payment_ticker=str(data["payment_ticker"]),
                    payment_asset_id=int(data["payment_asset_id"]),
                    price=int(data["price"]) if data["price"] is not None else 0,
                    qty=int(data["qty"]),
                    filled=int(data["filled"])
                )

                if order.price == 0:
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
