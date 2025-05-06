import os
from pydantic_settings import BaseSettings
from passlib.context import CryptContext
from fastapi_mail import ConnectionConfig
from authlib.integrations.starlette_client import OAuth


class Settings(BaseSettings):
    DATABASE_URL: str 
    
    OAUTH2_CLIENT_ID: str | None = None
    OAUTH2_CLIENT_SECRET: str | None = None
    
    SECRET_KEY: str 
    ALGORITHM: str
    SESSION_KEY: str

    EMAIL_HOST: str | None = None
    EMAIL_HOST_USER: str | None = None 
    EMAIL_HOST_PASSWORD: str | None = None
    EMAIL_PORT: int | None = None

    CELERY_REDIS_URL: str
    CELERY_RESULT_BACKEND: str

    MAX_ATTEMPTS: int
    BLOCK_TIME: int 
    WINDOW_TIME: int

    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    ADMIN_EMAIL: str
    ADMIN_NAME: str 
    ADMIN_PASSWORD: str

    BOOTSTRAP_SERVERS: str
    WALLET_EVENTS_TOPIC: str

    LOG_LEVEL: str = "INFO"

    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if settings.EMAIL_HOST:
    email_conf = ConnectionConfig(
        MAIL_USERNAME=settings.EMAIL_HOST_USER,
        MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
        MAIL_FROM=settings.EMAIL_HOST_USER,
        MAIL_PORT=settings.EMAIL_PORT,
        MAIL_SERVER=settings.EMAIL_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
    )

if settings.OAUTH2_CLIENT_SECRET:
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.OAUTH2_CLIENT_ID,
        client_secret=settings.OAUTH2_CLIENT_SECRET,
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        authorize_params={"scope": "openid email profile"},
        access_token_url="https://oauth2.googleapis.com/token",
        client_kwargs={"scope": "openid email profile"},
        server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration'
    )