from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.routers.api.v1 import auth
from app.routers.api.v1 import admin 
from app.utils.create_admin import create_first_admin
from app.core.config import settings
from app.core.logger import logger
from app.kafka.producers.send_user_event_producer import user_event_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_first_admin()
    except Exception as e:
        logger.error(f"⚠️ {e}")
    
    await user_event_producer.start()
    logger.info("Wallet Event Producer Started")

    yield

    await user_event_producer.stop()
    logger.info("Wallet Event Producer Stopped")


app = FastAPI(title="Auth Service", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(auth.router, prefix="/api/v1/public", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
