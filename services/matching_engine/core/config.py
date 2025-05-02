import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str

    BOOTSTRAP_SERVERS: str
    MARKET_QUOTE_REQUEST_TOPIC: str
    ORDERS_TOPIC: str
    ORDERS_UPDATE_TOPIC: str
    POST_TRADE_PROCESSING_TOPIC: str
    MARKET_QUOTE_RESPONSE_TOPIC: str
    TRANSACTIONS_TOPIC: str

    LOG_LEVEL: str = "INFO"

    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


settings = Settings()