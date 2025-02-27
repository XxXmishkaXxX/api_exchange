from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models.user import User
from app.models.password_reset import PasswordResetCode
from app.core.config import pwd_context
from datetime import datetime


class UserRepository:
    """Репозиторий для управления пользователями в базе данных."""
    
    def __init__(self, db: AsyncSession) -> None:
        """Инициализирует репозиторий с сессией базы данных.
        
        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
        """
        self.db = db

    async def create(self, user: User) -> User:
        """Создаёт нового пользователя в базе данных.
        
        Args:
            user (User): Объект пользователя.
        
        Returns:
            User: Созданный пользователь.
        
        Raises:
            ValueError: Если пользователь с таким email уже существует.
        """
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"User with email {user.email} already exists.")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по его ID.
        
        Args:
            user_id (int): Идентификатор пользователя.
        
        Returns:
            Optional[User]: Найденный пользователь или None, если не найден.
        """
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получает пользователя по email.
        
        Args:
            email (str): Электронная почта пользователя.
        
        Returns:
            Optional[User]: Найденный пользователь или None, если не найден.
        """
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def verify_password(self, provided_password: str, stored_password: str) -> bool:
        """Проверяет соответствие введённого пароля хешированному паролю в БД.
        
        Args:
            provided_password (str): Введённый пользователем пароль.
            stored_password (str): Захешированный пароль из базы данных.
        
        Returns:
            bool: True, если пароли совпадают, иначе False.
        """
        try:
            res = pwd_context.verify(provided_password, stored_password)
            return res
        except:
            return False
    
    def get_password_hash(self, password) -> str:
        """
        Функция для создания хэша пароля.

        :param password: Пароль пользователя.
        :return: Хэш строка
        """
        return pwd_context.hash(password)

    async def update_user(self, user_id: int, name: Optional[str] = None, password: Optional[str] = None) -> Optional[User]:
        """Обновляет данные пользователя (имя и/или пароль).
        
        Args:
            user_id (int): Идентификатор пользователя.
            name (Optional[str], optional): Новое имя. Defaults to None.
            password (Optional[str], optional): Новый пароль. Defaults to None.
        
        Returns:
            Optional[User]: Обновлённый пользователь или None, если пользователь не найден.
        """
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            if name:
                db_user.name = name
            if password:
                db_user.password = password
            await self.db.commit()
            await self.db.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: int) -> Optional[User]:
        """Удаляет пользователя из базы данных.
        
        Args:
            user_id (int): Идентификатор пользователя.
        
        Returns:
            Optional[User]: Удалённый пользователь или None, если пользователь не найден.
        """
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
        return db_user

    
    async def create_reset_code(self, user_id: int, reset_code: str, expires_at: datetime) -> PasswordResetCode:
        """Создаёт код сброса пароля и сохраняет его в базе данных.

        Args:
            user_id (int): Идентификатор пользователя.
            reset_code (str): Код сброса пароля.
            expires_at (datetime): Время истечения срока действия кода.

        Returns:
            PasswordResetCode: Созданный код сброса пароля.
        """
        reset_code_entry = PasswordResetCode(
            user_id=user_id,
            reset_code=reset_code,
            expires_at=expires_at
        )
        self.db.add(reset_code_entry)
        await self.db.commit()
        await self.db.refresh(reset_code_entry)
        return reset_code_entry

    async def get_reset_code(self, reset_code: str) -> Optional[PasswordResetCode]:
        """Ищет код сброса по значению кода.

        Args:
            reset_code (str): Код сброса пароля.

        Returns:
            Optional[PasswordResetCode]: Найденный код или None, если не найден.
        """
        result = await self.db.execute(select(PasswordResetCode).filter(PasswordResetCode.reset_code == reset_code))
        return result.scalars().first()

    async def delete_reset_code(self, reset_code: str) -> Optional[PasswordResetCode]:
        """Удаляет код сброса из базы данных.

        Args:
            reset_code (str): Код сброса пароля.

        Returns:
            Optional[PasswordResetCode]: Удалённый код сброса или None, если код не найден.
        """
        result = await self.db.execute(select(PasswordResetCode).filter(PasswordResetCode.reset_code == reset_code))
        reset_code_entry = result.scalars().first()
        if reset_code_entry:
            await self.db.delete(reset_code_entry)
            await self.db.commit()
        return reset_code_entry