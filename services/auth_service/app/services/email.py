from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import random
import string
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.models.email import EmailVerification
from app.repositories.user_repository import UserRepository
from app.repositories.email_repository import EmailRepository
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_HOST_USER,
    MAIL_PASSWORD=settings.EMAIL_HOST_PASSWORD,
    MAIL_FROM=settings.EMAIL_HOST_USER,
    MAIL_PORT=settings.EMAIL_PORT,
    MAIL_SERVER=settings.EMAIL_HOST,
    MAIL_TLS=True,
    MAIL_SSL=False,
)

mail = FastMail(conf)

class VerificationEmailService:

    def __init__(self, user_repo: UserRepository, email_repo: EmailRepository):
        self.user_repo = user_repo
        self.emai_repo = email_repo

    async def verify_email_code(self, verification_code: str):
        # Получаем запись о верификации по коду
        verification = await self.email_repo.get_verification_by_code(verification_code)

        if not verification:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Verification code has expired")

        user = await self.user_repo.get_user_by_id(verification.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_verified = True
        await self.user_repo.update_user(user)

        return {"message": "Email verified successfully"}

    async def send_verification_email(self, user_id: int, verification_code: str):
        # Получаем данные пользователя
        user = await self.user_repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Формируем сообщение
        message = MessageSchema(
            subject="Email Verification",
            recipients=[user.email],
            body=f"Your verification code is: {verification_code}",
            subtype="plain"
        )

        # Отправляем письмо
        await mail.send_message(message)

    async def resend_verification_email_code(self, user_id: int):
        # Проверяем существующую запись и удаляем если код истек
        verification = await self.email_repo.get_verification_by_user_id(user_id)

        if verification:
            # Удаляем истекший код
            await self.user_repo.delete_verification(verification)

        # Генерируем новый код
        new_verification_code = self.generate_new_code()

        # Создаем новый код подтверждения
        new_verification = EmailVerification(
            user_id=user_id,
            verification_code=new_verification_code,
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Код истекает через 1 час
        )
        await self.email_repo.add_verification(new_verification)

        # Отправляем новый код на почту
        await self.send_verification_email(user_id, new_verification_code)

        return {"message": "New verification code sent"}

    @staticmethod
    def generate_new_code(length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
