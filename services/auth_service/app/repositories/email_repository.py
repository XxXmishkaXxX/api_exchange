from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.email import EmailVerification


class EmailRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_verification_by_code(self, verification_code: str):
        result = await self.db.execute(select(EmailVerification).filter(EmailVerification.verification_code == verification_code))
        return result.scalars().first()

    async def get_verification_by_user_email(self, email):
        result = await self.db.execute(select(EmailVerification).filter(EmailVerification.user_email == email))
        return result.scalars().first()

    async def add_verification(self, verification: EmailVerification):
        self.db.add(verification)
        await self.db.commit()

    async def delete_verification(self, verification: EmailVerification):
        await self.db.delete(verification)
        await self.db.commit()
