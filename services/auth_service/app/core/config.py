import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Конфигурация для подключения к базе данных
    DATABASE_URL: str 
    
    # # Конфигурация для OAuth2
    OAUTH2_CLIENT_ID: str
    OAUTH2_CLIENT_SECRET: str
    
    # Секретный ключ для подписания JWT токенов
    SECRET_KEY: str 
    SESSION_KEY: str
    # # Конфигурация для отправки email
    EMAIL_HOST: str
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    EMAIL_PORT: int

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

