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

    #kafka
    BOOTSTRAP_SERVERS: str
    
    MARKET_QUOTE_RESPONSE_TOPIC: str
    MARKET_QUOTE_REQUEST_TOPIC: str
    
    LOCK_ASSETS_RESPONSE_TOPIC: str
    LOCK_ASSETS_REQUEST_TOPIC: str

    OREDER_STATUS_TOPIC: str
    ORDERS_TOPIC: str

    ASSET_TOPIC: str

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")