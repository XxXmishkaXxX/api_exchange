from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from redis import asyncio as aioredis


from app.core.config import settings
from app.core.logger import logger


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



class RedisConnectionPool:
    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.pool: aioredis.Redis = None

    async def start(self):
        """Подключение к Redis при старте приложения."""
        self.pool = aioredis.from_url(self.redis_url, decode_responses=True, max_connections=300)

    async def get_redis_connection(self) -> aioredis.Redis:
        if not self.pool:
            raise ConnectionError("Redis соединение не инициализировано!")
        return self.pool

    async def close(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def connection(self):
        redis = await self.get_redis_connection()
        try:
            yield redis
        finally:
            pass

redis_pool = RedisConnectionPool(settings.REDIS_URL)
