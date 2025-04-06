import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.routers.api.v1 import order
from app.core.config import settings
from app.core.logger import logger
from app.services.producer import lock_assets_producer, order_producer
from app.services.consumer import order_status_consumer, asset_consumer, change_balance_consumer
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
        await change_balance_consumer.start()
        asyncio.create_task(change_balance_consumer.consume_messages())
        logger.info("✅ Kafka Consumers started.")
        
        await lock_assets_producer.start()
        await order_producer.start()
        logger.info("✅ Kafka producers started.")
    
    except Exception as e:
        logger.warning(f"⚠️ Ошибка Kafka: {e}")

    yield
    
    await redis_pool.close()
    logger.info("🛑 Redis closed.")

    await order_producer.stop()
    await lock_assets_producer.stop()
    
    await change_balance_consumer.stop()
    await order_status_consumer.stop()
    await asset_consumer.stop()
    logger.info("🛑 Kafka Producer and Consumers stopped.")


app = FastAPI(title="Orders Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
