from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routers.api.v1 import order
from app.db.database import engine, Base
from app.core.config import settings



app = FastAPI(title="Orders Service")


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await create_tables()


app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(order.router, prefix="/api/v1/order", tags=["order"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
