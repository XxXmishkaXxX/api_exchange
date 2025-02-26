import jwt
import random
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.config import settings
from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.services.email import VerificationEmailService


# Инициализация контекста для работы с bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """
    Сервис для работы с пользователями, включающий операции аутентификации, изменения пароля и извлечения данных о текущем пользователе.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Инициализация сервиса пользователей.

        :param db: Экземпляр асинхронной сессии SQLAlchemy для взаимодействия с базой данных.
        """
        self.email_service = VerificationEmailService(db)
        self.user_repo = UserRepository(db)

    async def get_current_user(self, token: str) -> User:
        """
        Получает текущего пользователя, декодируя JWT токен.

        :param token: JWT токен, полученный при аутентификации.
        :return: Объект пользователя, соответствующий токену.
        :raises HTTPException: Если токен некорректен или пользователь не найден.
        """
        try:
            # Декодируем токен с помощью секретного ключа и алгоритма HS256
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature"
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Извлекаем email из декодированного токена
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Получаем пользователя по email
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    async def change_password(self, user_id: int, data: ChangePasswordRequest) -> User:
        """
        Меняет пароль пользователя, если старый пароль верный и оба новых пароля совпадают.

        :param user_id: Идентификатор пользователя, чей пароль нужно изменить.
        :param data: Данные, содержащие старый и новый пароли.
        :return: Обновленный объект пользователя с новым паролем.
        :raises HTTPException: Если старый пароль неверный, пароли не совпадают или произошла ошибка обновления пароля.
        """
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Проверка старого пароля
        if not pwd_context.verify(data.old_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password")
        
        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")

        # Хешируем новый пароль
        hashed_password = pwd_context.hash(data.new_password)
        
        # Обновляем пользователя с новым паролем
        updated_user = await self.user_repo.update_user(user_id, password=hashed_password)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        return updated_user


    async def forgot_password(self, data: ForgotPasswordRequest):
        """
        Запрос на сброс пароля. Генерирует код сброса и отправляет его на email пользователя.

        :param data: Запрос на сброс пароля, содержащий email пользователя.
        """
        # Поиск пользователя по email
        user = await self.user_repo.get_user_by_email(data.email)
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Генерация кода сброса
        reset_code = self.generate_reset_code()  # Генерация случайного кода
        expiration_time = datetime.utcnow() + timedelta(minutes=15)  # Код действует 15 минут
        
        # Сохранение кода сброса в базе данных
        reset_code_entry = await self.user_repo.create_reset_code(
            user_id=user.id,
            reset_code=reset_code,
            expires_at=expiration_time
        )
        
        # Отправка кода сброса на email
        await self.email_service.send_reset_email(user.email, reset_code)

        return {"detail": "Password reset code has been sent to your email."}


    async def confirm_reset_code(self, data: ResetCodeRequest):
        """
        Подтверждение кода сброса и обновление пароля пользователя.

        :param data: Запрос с кодом сброса и новыми паролями.
        """
        # Поиск кода сброса в базе данных
        reset_code_entry = await self.user_repo.get_reset_code(data.code)

        if not reset_code_entry:
            raise HTTPException(status_code=404, detail="Invalid or expired reset code")
        
        if reset_code_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Reset code has expired")
        
        # Получаем пользователя по user_id, связанному с кодом сброса
        user = await self.user_repo.get_user_by_id(reset_code_entry.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Проверка на совпадение нового пароля
        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")
        
        # Хешируем новый пароль
        hashed_password = pwd_context.hash(data.new_password)
        
        # Обновление пароля пользователя в базе данных
        updated_user = await self.user_repo.update_user(user.id, password=hashed_password)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        # Удаление кода сброса после использования
        await self.user_repo.delete_reset_code(data.code)

        return {"detail": "Password has been successfully reset."}
        
    def generate_reset_code(self, length: int = 6) -> str:
        """
        Генерирует случайный код сброса пароля.

        :param length: Длина кода сброса. По умолчанию 6 символов.
        :return: Генерируемый код сброса.
        """
        # Для простоты используем цифры
        return ''.join(random.choices(string.digits, k=length))