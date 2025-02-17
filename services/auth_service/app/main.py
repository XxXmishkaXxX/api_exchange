from fastapi import FastAPI
from app.routers import auth, oauth2
from app.db.database import engine, Base
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

app = FastAPI(title="Auth Service")

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_KEY)

# Подключаем маршруты
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(oauth2.router, prefix="/api/v1/oauth", tags=["oauth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)