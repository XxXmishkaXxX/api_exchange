import logging
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

from app.routers.api.v1 import auth as auth_v1
from app.routers.api.v2 import auth, oauth2, email, user
from app.admin.create_admin import create_first_admin
from app.core.config import settings
from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_first_admin()
    except Exception as e:
        logger.error(f"⚠️ {e}")

    yield


app = FastAPI(title="Auth Service", lifespan=lifespan)


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(auth_v1.router, prefix="/api/v1/public")

app.include_router(auth.router, prefix="/api/v2/auth", tags=["auth"])
app.include_router(oauth2.router, prefix="/api/v2/oauth", tags=["oauth"])
app.include_router(email.router, prefix="/api/v2/mail", tags=["mail"])
app.include_router(user.router, prefix="/api/v2/user", tags=["user"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
