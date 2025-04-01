from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from redis import asyncio as aioredis
from contextlib import asynccontextmanager


from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=50,
    max_overflow=100,
    pool_recycle=300,
    pool_timeout=30
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session



@asynccontextmanager
async def get_redis_connection():
    """Генератор для подключения к Redis с пулом соединений."""
    redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=100
    )
    try:
        yield redis
    finally:
        await redis.close()
