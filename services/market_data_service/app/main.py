import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers.api.v1 import md_admins, md_users
from app.services.producer import producer_service



@asynccontextmanager
async def lifespan(app: FastAPI):

    yield

    await producer_service.close()



app = FastAPI(title="Market Data Service")

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)
app.include_router(md_users.router, prefix="/api/v1/public", tags=["market_data"])
app.include_router(md_admins.router, prefix="/api/v1/admin", tags=["market_data"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
