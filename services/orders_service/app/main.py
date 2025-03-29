import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.routers.api.v1 import order
from app.db.database import engine, Base
from app.core.config import settings
from app.services.producer import producer_service
from app.services.consumer import consumer_service



async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    try:
        await consumer_service.start()
        asyncio.create_task(consumer_service.consume_messages())
        print("✅ Kafka Consumer started.")
    except Exception as e:
        print(f"⚠️ Ошибка Kafka: {e}")

    yield

    await producer_service.close()
    await consumer_service.stop()
    print("🛑 Kafka Producer and Consumer stopped.")


app = FastAPI(title="Orders Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
