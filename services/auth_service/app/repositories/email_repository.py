from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.email import EmailVerification
from typing import Optional


class EmailRepository:
    """
    Репозиторий для работы с таблицей EmailVerification в базе данных.

    Предоставляет методы для получения, добавления и удаления записей в базе данных.
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализация репозитория с асинхронной сессией базы данных.

        :param db: Асинхронная сессия SQLAlchemy.
        """
        self.db = db

    async def get_verification_by_code(self, verification_code: str) -> Optional[EmailVerification]:
        """
        Получение записи о верификации по коду верификации.

        :param verification_code: Код верификации.
        :return: Объект EmailVerification или None, если не найдено.
        """
        result = await self.db.execute(select(EmailVerification).filter(EmailVerification.verification_code == verification_code))
        return result.scalars().first()

    async def get_verification_by_user_email(self, email: str) -> Optional[EmailVerification]:
        """
        Получение записи о верификации по email пользователя.

        :param email: Адрес электронной почты пользователя.
        :return: Объект EmailVerification или None, если не найдено.
        """
        result = await self.db.execute(select(EmailVerification).filter(EmailVerification.user_email == email))
        return result.scalars().first()

    async def add_verification(self, verification: EmailVerification) -> None:
        """
        Добавление записи о верификации в базу данных.

        :param verification: Объект EmailVerification для добавления.
        :return: None.
        """
        self.db.add(verification)
        await self.db.commit()

    async def delete_verification(self, verification: EmailVerification) -> None:
        """
        Удаление записи о верификации из базы данных.

        :param verification: Объект EmailVerification для удаления.
        :return: None.
        """
        await self.db.delete(verification)
        await self.db.commit()
