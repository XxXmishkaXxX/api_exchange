import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routers.api.v1 import wallet_users, wallet_admins
from app.core.config import settings
from app.core.logger import logger
from app.services.consumers import  assets_consumer
from app.db.database import redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_pool.start()
        logger.info("✅ Redis started.")
        # await change_assets_consumer.start()
        # asyncio.create_task(change_assets_consumer.consume_messages())
        # await lock_assets_consumer.start()
        # asyncio.create_task(lock_assets_consumer.consume_messages())
        await assets_consumer.start()
        asyncio.create_task(assets_consumer.consume_messages())
        logger.info("✅ Kafka Consumers started.")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка Kafka: {e}")

    yield

    # await change_assets_consumer.stop()
    # await lock_assets_consumer.stop()
    await assets_consumer.stop()
    logger.info("🛑 Consumers stopped.")
    await redis_pool.close()
    logger.info("🛑 Redis stopped.")


app = FastAPI(title="Wallet Service", lifespan=lifespan)


app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(wallet_users.router, prefix="/api/v1/balance", tags=["wallet"])
app.include_router(wallet_admins.router, prefix="/api/v1/admin/balance", tags=["wallet"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
