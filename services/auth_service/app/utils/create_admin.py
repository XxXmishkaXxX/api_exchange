from sqlalchemy.future import select
from uuid import UUID

from app.models.user import User
from app.core.config import settings
from app.db.database import get_db
from app.models.user import Role
from app.core.logger import logger
from app.utils.create_jwt import create_api_key



async def create_first_admin() -> None:
    try:
        async for session in get_db():
            result = await session.execute(select(User).filter(User.role == Role.ADMIN))
            superuser = result.scalars().first()

            if superuser is None:
                new_superuser = User(
                    name=settings.ADMIN_NAME,
                    role=Role.ADMIN,
                )
                session.add(new_superuser)
                await session.flush()

                api_key = create_api_key(user_id=new_superuser.id, role=Role.ADMIN)
                
                new_superuser.api_key = api_key

                await session.commit()
                logger.info("Администратор успешно создан")
            else:
                logger.info("Администратор уже существует")
    except Exception as e:
        logger.error(f"Ошибка при создании администратора: {e}")
        raise e