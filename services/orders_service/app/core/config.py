import os
from pydantic_settings import BaseSettings
from passlib.context import CryptContext

class Settings(BaseSettings):
    DATABASE_URL: str 
    REDIS_URL: str

    SECRET_KEY: str 
    SESSION_KEY: str
    ALGORITHM: str

    BOOTSTRAP_SERVERS: str
    
    MARKET_QUOTE_RESPONSE_TOPIC: str
    MARKET_QUOTE_REQUEST_TOPIC: str
    
    LOCK_ASSETS_RESPONSE_TOPIC: str
    LOCK_ASSETS_REQUEST_TOPIC: str

    OREDER_STATUS_TOPIC: str
    ORDERS_TOPIC: str

    ASSET_TOPIC: str

    USER_EVENTS_TOPIC: str

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")