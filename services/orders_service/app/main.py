import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.routers.api.v1 import order
from app.core.config import settings
from app.core.logger import logger
from app.kafka.producers.lock_assets_producer import lock_assets_producer
from app.kafka.producers.market_quote_producer import market_quote_producer
from app.kafka.producers.order_producer import order_producer
from app.kafka.consumers.lock_assets_consumer import lock_response_consumer 
from app.kafka.consumers.order_status_consumer import order_status_consumer
from app.kafka.consumers.assets_consumer import asset_consumer
from app.kafka.consumers.market_quote_consumer import market_quote_response_consumer
from app.kafka.consumers.cancel_orders_consumer import cancel_user_orders_consumer
from app.db.database import redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_pool.start()
        logger.info("✅ Redis started.")
        
        await order_status_consumer.start()
        asyncio.create_task(order_status_consumer.consume_messages())
        await asset_consumer.start()
        asyncio.create_task(asset_consumer.consume_messages())
        await lock_response_consumer.start()
        asyncio.create_task(lock_response_consumer.consume_messages())
        await market_quote_response_consumer.start()
        asyncio.create_task(market_quote_response_consumer.consume_messages())
        await cancel_user_orders_consumer.start()
        asyncio.create_task(cancel_user_orders_consumer.consume_messages())
        logger.info("✅ Kafka Consumers started.")
        
        await lock_assets_producer.start()
        await order_producer.start()
        await market_quote_producer.start()
        logger.info("✅ Kafka producers started.")
    
    except Exception as e:
        logger.warning(f"⚠️ Ошибка Kafka: {e}")

    yield
    
    await redis_pool.close()
    logger.info("🛑 Redis closed.")

    await order_producer.stop()
    await lock_assets_producer.stop()
    await market_quote_producer.stop()
    
    await cancel_user_orders_consumer.stop()
    await market_quote_response_consumer.stop()
    await lock_response_consumer.stop()
    await order_status_consumer.stop()
    await asset_consumer.stop()
    logger.info("🛑 Kafka Producer and Consumers stopped.")


app = FastAPI(title="Orders Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
