import asyncio
import logging
from kafka.consumer import OrderConsumerService, MarketQuoteRequestConsumer
from kafka.producers import KafkaOrderProducer, KafkaWalletProducer, KafkaMarketQuoteResponseProducer, KafkaSendTransactionProducer
from redis_client.redis_client import AsyncRedisOrderClient
from engine.matching_engine import MatchingEngine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_producers():
    """Создаёт и запускает все Kafka продюсеры."""
    try:
        prod_order = KafkaOrderProducer()
        await prod_order.start()
        prod_wallet = KafkaWalletProducer()
        await prod_wallet.start()
        prod_market_quote = KafkaMarketQuoteResponseProducer()
        await prod_market_quote.start()
        prod_transaction = KafkaSendTransactionProducer()
        await prod_transaction.start()
        return prod_order, prod_wallet, prod_market_quote, prod_transaction
    except Exception as e:
        logger.error(f"❌ Error starting Kafka producers: {e}")
        raise

async def create_redis_client():
    """Создаёт асинхронное подключение к Redis."""
    try:
        redis_client = AsyncRedisOrderClient("redis_me")
        await redis_client.connect()
        await redis_client.redis_client.ping()
        logger.info(f"✅ Подключение к Redis установлено.")
        return redis_client
    except Exception as e:
        logger.error(f"❌ Error connecting to Redis: {e}")
        raise

async def create_matching_engine(prod_order, prod_wallet, prod_market_quote, prod_transaction, redis_client):
    """Создаёт экземпляр MatchingEngine и восстанавливает ордербуки из Redis."""
    try:
        engine = MatchingEngine(
            change_order_status_prod=prod_order, 
            post_wallet_transfer_prod=prod_wallet, 
            prod_market_quote=prod_market_quote,
            prod_transaction=prod_transaction,
            redis=redis_client
        )
        logger.info("Движок создан")
        await engine.restore_order_books_from_redis()
        return engine
    except Exception as e:
        logger.error(f"❌ Error creating MatchingEngine: {e}")
        raise

async def start_consumers_services(engine):
    """Запускает Kafka consumer service в отдельных задачах."""
    try:
        order_consumer_service = OrderConsumerService(engine)
        market_quote_request_consumer_service = MarketQuoteRequestConsumer(engine)

        order_task = asyncio.create_task(order_consumer_service.start())
        quote_task = asyncio.create_task(market_quote_request_consumer_service.start())

        logger.info("✅ Kafka consumers запущены.")

        await asyncio.gather(order_task, quote_task)
    except Exception as e:
        logger.error(f"❌ Error starting KafkaConsumerService: {e}")
        raise

async def main():
    """Основной асинхронный процесс приложения."""
    try:
        # Создаём продюсеров
        prod_order, prod_wallet, prod_market_quote, prod_transaction = await create_producers()
        
        # Создаём Redis клиент
        redis_client = await create_redis_client()
        
        # Создаём MatchingEngine с подключением к Redis
        engine = await create_matching_engine(prod_order, prod_wallet, prod_market_quote, prod_transaction, redis_client)
        
        # Запускаем сервисы потребителей Kafka
        await start_consumers_services(engine)
    except Exception as e:
        logger.error(f"❌ Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())


