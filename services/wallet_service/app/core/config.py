import os
from pydantic_settings import BaseSettings
from passlib.context import CryptContext

class Settings(BaseSettings):

    DATABASE_URL: str 
    REDIS_URL: str

    #kafka
    BOOTSTRAP_SERVERS: str
    LOCK_ASSETS_RESPONSE_TOPIC: str
    LOCK_ASSETS_REQUEST_TOPIC:  str
    ASSET_TOPIC: str
    POST_TRADE_PROCESSING_TOPIC: str
    WALLET_EVENTS_TOPIC: str

    SECRET_KEY: str 
    SESSION_KEY: str
    ALGORITHM: str

    LOG_LEVEL: str = "INFO"

    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


