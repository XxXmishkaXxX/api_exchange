from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from app.routers import auth, oauth2, email, user
from app.db.database import engine, Base
from app.core.config import settings
from app.core.limiter import limiter
from app.middleware.ratelimit import RateLimitMiddleware



app = FastAPI(title="Auth Service")


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RateLimitMiddleware)


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

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(oauth2.router, prefix="/api/v1/oauth", tags=["oauth"])
app.include_router(email.router, prefix="/api/v1/mail", tags=["mail"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
