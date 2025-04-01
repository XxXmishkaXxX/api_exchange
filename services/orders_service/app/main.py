import asyncio
import logging
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.routers.api.v1 import order
from app.core.config import settings
from app.core.logger import logger
from app.services.producer import producer_service
from app.services.consumer import order_status_consumer, ticker_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await order_status_consumer.start()
        asyncio.create_task(order_status_consumer.consume_messages())
        await ticker_consumer.start()
        asyncio.create_task(ticker_consumer.consume_messages())
        logger.info("✅ Kafka Consumers started.")
        await producer_service.start()
        logger.info("✅ Kafka producer started.")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка Kafka: {e}")

    yield

    await producer_service.stop()
    await order_status_consumer.stop()
    await ticker_consumer.stop()
    logger.info("🛑 Kafka Producer and Consumers stopped.")


app = FastAPI(title="Orders Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
