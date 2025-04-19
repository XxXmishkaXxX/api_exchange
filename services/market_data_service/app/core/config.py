import os
from pydantic_settings import BaseSettings
from passlib.context import CryptContext

class Settings(BaseSettings):
    # Конфигурация для подключения к базе данных
    DATABASE_URL: str 
    REDIS_URL: str
    # Секретный ключ для подписания JWT токенов
    SECRET_KEY: str 
    SESSION_KEY: str
    ALGORITM_JWT: str

    BOOTSTRAP_SERVERS: str

    # Логирование
    LOG_LEVEL: str = "INFO"

    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        # Чтение значений из .env файла
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


# Получение настроек через Pydantic
settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")