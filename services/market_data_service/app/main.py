import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers.api.v1 import md_admins, md_users
from app.kafka.producers.assets_producer import assets_producer
from app.db.database import redis_pool
from app.kafka.consumers.transactions_consumer import transaction_consumer
from app.core.logger import logger



@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_pool.start()
        logger.info("✅ Redis connected.")

        await assets_producer.start()
        logger.info("✅ Kafka producer started.")

        await transaction_consumer.start()
        logger.info("✅ Kafka consumer started.")

        asyncio.create_task(transaction_consumer.consume_messages())
        logger.info("⏳ Kafka consumer message loop started.")

        yield

    except Exception as e:
        logger.error(f"❌ Ошибка в lifespan: {e}", exc_info=True)
        raise

    finally:
        await assets_producer.stop()
        logger.info("🛑 Kafka producer закрыт.")

        await transaction_consumer.stop()
        logger.info("🛑 Kafka consumer остановлен.")

        await redis_pool.close()
        logger.info("🛑 Redis отключён.")



app = FastAPI(title="Market Data Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)
app.include_router(md_users.router, prefix="/api/v1/public", tags=["market_data"])
app.include_router(md_admins.router, prefix="/api/v1/admin", tags=["market_data"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
