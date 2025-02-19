from fastapi import FastAPI
from app.routers import auth, oauth2, email
from app.db.database import engine, Base
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

app = FastAPI(title="Auth Service")

# Асинхронная функция для создания таблиц
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Запуск создания таблиц
@app.on_event("startup")
async def on_startup():
    await create_tables()

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

# Подключаем маршруты
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(oauth2.router, prefix="/api/v1/oauth", tags=["oauth"])
app.include_router(email.router, prefix="/api/v1/mail", tags=["mail"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
