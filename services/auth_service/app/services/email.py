import random
import string
from datetime import datetime, timedelta

from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailVerification
from app.repositories.user_repository import UserRepository
from app.repositories.email_repository import EmailRepository
from app.core.config import settings
from app.schemas.email import VerificationRequest, ResendVerificationRequest

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_HOST_USER,
    MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
    MAIL_FROM=settings.EMAIL_HOST_USER,
    MAIL_PORT=settings.EMAIL_PORT,
    MAIL_SERVER=settings.EMAIL_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

mail = FastMail(conf)


class VerificationEmailService:
    """
    Сервис для отправки и проверки кодов подтверждения электронной почты.

    Этот сервис обрабатывает генерацию, отправку, проверку и повторную отправку кодов подтверждения
    для подтверждения учетной записи пользователя.

    Атрибуты:
        user_repo (UserRepository): Репозиторий для работы с данными пользователей.
        email_repo (EmailRepository): Репозиторий для работы с данными о подтверждении электронной почты.
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализация сервиса для подтверждения электронной почты с использованием сессии базы данных.

        Аргументы:
            db (AsyncSession): Сессия базы данных для взаимодействия с базой данных.
        """
        self.user_repo = UserRepository(db)
        self.email_repo = EmailRepository(db)

    async def verify_email_code(self, data: VerificationRequest) -> dict:
        """
        Проверяет код подтверждения, введенный пользователем.

        Аргументы:
            data (VerificationRequest): Данные запроса, содержащие email и код подтверждения.

        Возвращает:
            dict: Сообщение, указывающее на успешность или неудачу проверки.
        """
        verification = await self.email_repo.get_verification_by_user_email(data.email)

        if not verification:
            raise HTTPException(status_code=400, detail="Неверный код подтверждения")

        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Код подтверждения истек")

        user = await self.user_repo.get_user_by_id(verification.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user.is_verified = True
        await self.user_repo.update_user(user.id)
        await self.email_repo.delete_verification(verification)

        return {"message": "Электронная почта успешно подтверждена"}

    async def send_verification_email(self, user_id: int, user_email: str) -> None:
        """
        Отправляет письмо с кодом подтверждения на электронную почту пользователя.

        Аргументы:
            user_id (int): Идентификатор пользователя.
            user_email (str): Электронная почта пользователя.

        Исключения:
            HTTPException: Если пользователь не найден в базе данных.
        """
        user = await self.user_repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        code = self.generate_new_code()

        verification = EmailVerification(
            user_id=user_id,
            user_email=user_email,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=50)
        )

        await self.email_repo.add_verification(verification)

        message = MessageSchema(
            subject="Подтверждение электронной почты",
            recipients=[user.email],
            body=f"Ваш код подтверждения: {code}",
            subtype="plain"
        )

        await mail.send_message(message)

    async def resend_verification_email_code(self, data: ResendVerificationRequest) -> dict:
        """
        Отправляет новый код подтверждения на электронную почту пользователя.

        Аргументы:
            data (ResendVerificationRequest): Данные запроса, содержащие email пользователя.

        Возвращает:
            dict: Сообщение, указывающее на успешность или неудачу отправки кода подтверждения.
        """
        verification = await self.email_repo.get_verification_by_user_email(data.email)

        if not verification:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user_id = verification.user_id
        
        await self.email_repo.delete_verification(verification)

        await self.send_verification_email(user_id, data.email)

        return {"message": "Новый код подтверждения отправлен"}

    @staticmethod
    def generate_new_code(length: int = 6) -> str:
        """
        Генерирует новый код подтверждения.

        Аргументы:
            length (int): Длина генерируемого кода. По умолчанию 6.

        Возвращает:
            str: Сгенерированный код.
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
