import json
from aiokafka import AIOKafkaProducer

class BaseKafkaProducer:
    def __init__(self, topic: str):
        self.topic = topic
        self.producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send(self, message: dict):
        encoded = json.dumps(message).encode("utf-8")
        await self.producer.send(self.topic, encoded)

class KafkaOrderProducer(BaseKafkaProducer):
    def __init__(self):
        super().__init__(topic="orders_update")

    async def send_order_update(self, message):
        await self.send(message)

class KafkaWalletProducer(BaseKafkaProducer):
    def __init__(self):
        super().__init__(topic="post_trade_processing")

    async def send_wallet_update(self, transfer: dict):
        await self.send(transfer)


class KafkaMarketQuoteResponseProducer(BaseKafkaProducer):
    def __init__(self):
        super().__init__(topic="market_quote.response")
    
    async def send_market_quote_response(self, market_quote: dict):
        await self.send(market_quote)


class KafkaSendTransactionProducer(BaseKafkaProducer):
    def __init__(self):
        super().__init__(topic="transactions")
    
    async def send_transaction(self, transaction: dict):
        await self.send(transaction)