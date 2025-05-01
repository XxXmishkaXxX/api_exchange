import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routers.api.v1 import wallet_users, wallet_admins
from app.core.config import settings
from app.core.logger import logger
from app.db.database import redis_pool
from app.kafka.producers.lock_user_assets_producer import lock_uab_resp_producer
from app.kafka.consumers.assets_consumer import assets_consumer 
from app.kafka.consumers.lock_assets_consumer import  lock_asset_amount_consumer
from app.kafka.consumers.change_balance_consumer import change_balance_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_pool.start()
        logger.info("✅ Redis started.")
        
        await lock_uab_resp_producer.start()
        logger.info("✅ Kafka Producer started.")

        await change_balance_consumer.start()
        asyncio.create_task(change_balance_consumer.consume_messages())
        logger.info("✅ ChangeBalance Consumer started.")
        
        await assets_consumer.start()
        asyncio.create_task(assets_consumer.consume_messages())
        logger.info("✅ Assets Consumer started.")

        await lock_asset_amount_consumer.start()
        asyncio.create_task(lock_asset_amount_consumer.consume_messages())
        logger.info("✅ Lock Asset Amount Consumer started.")
        
    except Exception as e:
        logger.error(f"⚠️ Ошибка при запуске сервисов: {e}")
        raise e

    yield

    try:
        await change_balance_consumer.stop()
        logger.info("🛑 Change Balance Consumer stopped.")

        await lock_asset_amount_consumer.stop()
        logger.info("🛑 Lock Asset Amount Consumer stopped.")
        
        await assets_consumer.stop()
        logger.info("🛑 Assets Consumer stopped.")

        await lock_uab_resp_producer.stop()
        logger.info("🛑 Kafka Producer stopped.")
        
        await redis_pool.close()
        logger.info("🛑 Redis stopped.")
    except Exception as e:
        logger.error(f"⚠️ Ошибка при остановке сервисов: {e}")


app = FastAPI(title="Wallet Service", lifespan=lifespan)


app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(wallet_users.router, prefix="/api/v1/balance", tags=["wallet"])
app.include_router(wallet_admins.router, prefix="/api/v1/admin/balance", tags=["wallet"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
