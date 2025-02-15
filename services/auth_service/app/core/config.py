import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Конфигурация для подключения к базе данных
    DATABASE_URL: str 
    
    # # Конфигурация для OAuth2 (например, секретный ключ и параметры)
    # OAUTH2_CLIENT_ID: str
    # OAUTH2_CLIENT_SECRET: str
    # OAUTH2_AUTHORIZE_URL: str
    # OAUTH2_TOKEN_URL: str
    
    # Секретный ключ для подписания JWT токенов
    SECRET_KEY: str 
    
    # # Конфигурация для отправки email (например, SMTP сервер)
    # SMTP_SERVER: str
    # SMTP_PORT: int
    # SMTP_USER: str
    # SMTP_PASSWORD: str
    
    # Логирование
    LOG_LEVEL: str = "INFO"

    # Другие переменные окружения
    DEBUG: bool = False
    TESTING: bool = False

    class Config:
        # Чтение значений из .env файла
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')


# Получение настроек через Pydantic
settings = Settings()

