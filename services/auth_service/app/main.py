from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from app.routers.auth import router as auth_router
from app.routers.oauth2 import router as oauth2_router
from app.routers.email import router as email_router
from app.routers.user import router as user_router
from app.db.database import engine, Base
from app.core.config import settings
from app.core.limiter import limiter



app = FastAPI(title="Auth Service")


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await create_tables()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(oauth2_router, prefix="/api/v1/oauth", tags=["oauth"])
app.include_router(email_router, prefix="/api/v1/mail", tags=["mail"])
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
