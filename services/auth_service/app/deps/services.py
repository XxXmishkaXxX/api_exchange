from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.auth import AuthService
from app.services.email import EmailService
from app.services.user import UserService
from app.repositories import user_repository, email_repository


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Функция для получения экземпляра AuthService с зависимостями.
    
    Args:
        session (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).
    
    Returns:
        AuthService: Экземпляр сервиса аутентификации.
    """
    repository = user_repository.UserRepository(session)
    return AuthService(repository)


def get_email_service(session: AsyncSession = Depends(get_db)) -> EmailService:
    """Функция для получения экземпляра VerificationEmailService с зависимостями.
    
    Аргументы:
        session (AsyncSession, optional): Сессия базы данных. Defaults to Depends(get_db).
    
    Возвращает:
        VerificationEmailService: Экземпляр сервиса подтверждения электронной почты.
    """
    email_repo = email_repository.EmailRepository(session)
    return EmailService(email_repo)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Создает и возвращает сервис пользователя, инкапсулируя все зависимости, включая
    доступ к базе данных и сервис подтверждения email.

    :param db: Асинхронная сессия базы данных, автоматически передаваемая через Depends.
    :return: Экземпляр UserService, готовый к использованию в обработчиках запросов.
    """

    user_repo = user_repository.UserRepository(db)
    return UserService(user_repo)