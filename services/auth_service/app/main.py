from fastapi import FastAPI
from app.routers import auth
from app.db.database import engine, Base

app = FastAPI(title="Auth Service")

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

# Подключаем маршруты
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)