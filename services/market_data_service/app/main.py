import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.db.database import engine, Base
from app.core.config import settings



async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield



app = FastAPI(title="Market Data Service")

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
