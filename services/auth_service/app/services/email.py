import random
import string
from datetime import datetime, timedelta

from fastapi import HTTPException

from app.models.email import EmailVerification
from app.repositories.email_repository import EmailRepository
from app.schemas.email import VerificationRequest, ResendVerificationRequest
from app.tasks.tasks import send_email_task


class EmailService:
    """
    Сервис для отправки и проверки кодов подтверждения электронной почты.

    Этот сервис обрабатывает генерацию, отправку, проверку и повторную отправку кодов подтверждения
    для подтверждения учетной записи пользователя.

    Атрибуты:
        email_repo (EmailRepository): Репозиторий для работы с данными о подтверждении электронной почты.
    """

    def __init__(self, email_repo: EmailRepository) -> None:
        """
        Инициализация сервиса для подтверждения электронной почты с использованием сессии базы данных.

        Аргументы:
            email_repo (EmailRepository): Репозиторий электронной почты для работы с подтверждениями email.
        """
        self.email_repo = email_repo

    async def verify_email_code(self, data: VerificationRequest) -> dict:
        """
        Проверяет код подтверждения, введенный пользователем.

        Аргументы:
            data (VerificationRequest): Данные запроса, содержащие email и код подтверждения.

        Возвращает:
            dict: Сообщение, указывающее на успешность или неудачу проверки.
        
        Исключения:
            HTTPException: Если код подтверждения неверный или истек.
        """
        verification = await self.email_repo.get_verification_by_user_email(data.email)

        if not verification or verification.verification_code != data.verification_code:
            raise HTTPException(status_code=400, detail="Неверный код подтверждения")
        
        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Код подтверждения истек")

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
        code = self.generate_new_code()

        verification = EmailVerification(
            user_id=user_id,
            user_email=user_email,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=50)
        )

        await self.email_repo.add_verification(verification)

        message = {
            "subject": "Подтверждение электронной почты",
            "recipients": [user_email],
            "body": f"Ваш код подтверждения: {code}",
            "subtype": "plain"
        }

        send_email_task.apply_async(args=[message])

    async def resend_verification_email_code(self, data: ResendVerificationRequest) -> dict:
        """
        Отправляет новый код подтверждения на электронную почту пользователя.

        Аргументы:
            data (ResendVerificationRequest): Данные запроса, содержащие email пользователя.

        Возвращает:
            dict: Сообщение, указывающее на успешность или неудачу отправки кода подтверждения.

        Исключения:
            HTTPException: Если пользователь не найден или код подтверждения не был найден.
        """
        verification = await self.email_repo.get_verification_by_user_email(data.email)

        if not verification:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user_id = verification.user_id
        
        await self.email_repo.delete_verification(verification)

        await self.send_verification_email(user_id, data.email)

        return {"message": "Новый код подтверждения отправлен"}
    
    async def send_reset_email(self, user_email: str, reset_code: str) -> None:
        """
        Отправляет письмо с кодом для сброса пароля на электронную почту пользователя.

        Аргументы:
            user_email (str): Электронная почта пользователя.
            reset_code (str): Код для сброса пароля.

        Исключения:
            HTTPException: Если не удалось отправить письмо.
        """
        message = {
            "subject": "Сброс пароля",
            "recipients": [user_email],
            "body": f"Ваш код подтверждения: {reset_code}",
            "subtype": "plain"
        }

        send_email_task.apply_async(args=[message])

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
