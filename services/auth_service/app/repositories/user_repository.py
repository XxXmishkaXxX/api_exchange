from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import Optional
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        return pwd_context.verify(provided_password, stored_password)

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
                db_user.password = pwd_context.hash(password)
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
