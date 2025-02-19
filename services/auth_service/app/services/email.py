from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import random
import string
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.models.email import EmailVerification
from app.repositories.user_repository import UserRepository
from app.repositories.email_repository import EmailRepository
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.email import VerificationRequest

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

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.email_repo = EmailRepository(db)

    async def verify_email_code(self, data: VerificationRequest):
        verification = await self.email_repo.get_verification_by_user_email(data.email)

        if not verification:
            return {"error": "Invalid verification code"}

        if verification.expires_at < datetime.utcnow():
            return {"error": "Verification code has expired"}

        user = await self.user_repo.get_user_by_id(verification.user_id)

        if not user:
            return {"error": "User not found"}

        user.is_verified = True
        await self.user_repo.update_user(user.id)

        return {"message": "Email verified successfully"}

    async def send_verification_email(self, user_id: int, user_email: str):
        user = await self.user_repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        code = self.generate_new_code()

        verification = EmailVerification(
            user_id=user_id,
            user_email=user_email,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=50)
        )

        await self.email_repo.add_verification(verification)

        message = MessageSchema(
            subject="Email Verification",
            recipients=[user.email],
            body=f"Your verification code is: {code}",
            subtype="plain"
        )

        await mail.send_message(message)

    async def resend_verification_email_code(self, user_id: int):
        verification = await self.email_repo.get_verification_by_user_id(user_id)

        if verification:
            await self.user_repo.delete_verification(verification)

        new_verification_code = self.generate_new_code()

        new_verification = EmailVerification(
            user_id=user_id,
            verification_code=new_verification_code,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        await self.email_repo.add_verification(new_verification)

        await self.send_verification_email(user_id)

        return {"message": "New verification code sent"}

    @staticmethod
    def generate_new_code(length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
