from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Загружаем переменные окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db_name")

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс моделей
Base = declarative_base()

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
