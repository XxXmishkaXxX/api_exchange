import logging
from sqlalchemy.future import select


from app.models.user import User
from app.core.config import settings, pwd_context
from app.db.database import get_db
from app.models.user import Role
from app.core.logger import logger


async def create_first_admin() -> None:
    try:
        async for session in get_db():
            result = await session.execute(select(User).filter(User.role == Role.ADMIN))
            superuser = result.scalars().first()

            if superuser is None:
                hashed_password = pwd_context.hash(settings.ADMIN_PASSWORD)
                new_superuser = User(
                    email=settings.ADMIN_EMAIL,
                    name=settings.ADMIN_NAME, 
                    password=hashed_password, 
                    role=Role.ADMIN, 
                    is_verified=True
                )
                session.add(new_superuser)
                await session.commit()
                logger.info("Администратор успешно создан")
            else:
                logger.info("Администратор уже существует")
    except Exception as e:
        logger.error(f"Ошибка при создании администратора: {e}")
        raise e