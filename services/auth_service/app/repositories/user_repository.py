from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User):
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"User with email {user.email} already exists.")

    async def get_user_by_id(self, user_id: int):
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def verify_password(self, provided_password: str, stored_password: str) -> bool:
        return pwd_context.verify(provided_password, stored_password)

    async def update_user(self, user_id: int, name: str = None, password: str = None):
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            if name:
                db_user.name = name
            if password:
                db_user.password = pwd_context.hash(password)
            await self.db.commit()
            await self.db.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: int):
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
        return db_user