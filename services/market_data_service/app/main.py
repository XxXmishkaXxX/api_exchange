import asyncio
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):

    yield



app = FastAPI(title="Market Data Service")

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
