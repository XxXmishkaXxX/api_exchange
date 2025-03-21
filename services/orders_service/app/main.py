import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routers.api.v1 import order
from app.db.database import engine, Base
from app.core.config import settings
from app.services.producer import producer_service
from app.services.consumer import consumer_service


app = FastAPI(title="Orders Service")



async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        

@app.on_event("startup")
async def on_startup():
    await create_tables()
    await producer_service.start()
    await consumer_service.start()
    print("Kafka Producer initialized.")

    asyncio.create_task(consumer_service.consume_messages())



@app.on_event("shutdown")
async def shutdown_event():
    await producer_service.stop()



app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
