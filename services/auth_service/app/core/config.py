import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str 

    SECRET_KEY: str 
    ALGORITHM: str
    SESSION_KEY: str

    ADMIN_NAME: str 

    BOOTSTRAP_SERVERS: str
    USER_EVENTS_TOPIC: str

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

settings = Settings()