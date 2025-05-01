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
    ALGORITHM: str

    BOOTSTRAP_SERVERS: str
    TRANSACTIONS_TOPIC: str
    ASSET_TOPIC: str

    # Логирование
    LOG_LEVEL: str = "INFO"

    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")