import jwt
import random
import string
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.config import settings
from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.services.email import EmailService, get_email_service
from app.db.database import get_db


class UserService:
    """
    Сервис для работы с пользователями, включающий операции аутентификации, изменения пароля и извлечения данных о текущем пользователе.
    """

    def __init__(self, user_repo: UserRepository, email_service: EmailService) -> None:
        """
        Инициализация сервиса пользователей.

        :param user_repo: Репозиторий для работы с пользователями.
        :param email_service: Сервис для работы с подтверждениями email.
        """
        self.email_service = email_service
        self.user_repo = user_repo

    async def get_current_user(self, token: str) -> User:
        """
        Получает текущего пользователя, декодируя JWT токен.

        :param token: JWT токен, полученный при аутентификации.
        :return: Объект пользователя, соответствующий токену.
        :raises HTTPException: Если токен некорректен, истек или пользователь не найден.
        """
        try:
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

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    async def change_password(self, user_id: int, data: ChangePasswordRequest) -> dict:
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
        
        if not await self.user_repo.verify_password(data.old_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password")
        
        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")

        updated_user = await self.user_repo.update_user(user_id, 
                                                        password=self.user_repo.get_password_hash(data.new_password))
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        return {"message": "Password has changed"}

    async def forgot_password(self, data: ForgotPasswordRequest):
        """
        Запрос на сброс пароля. Генерирует код сброса и отправляет его на email пользователя.

        :param data: Запрос на сброс пароля, содержащий email пользователя.
        :raises HTTPException: Если пользователь не найден.
        """
        user = await self.user_repo.get_user_by_email(data.email)
        
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        reset_code = self.generate_reset_code()  # Генерация случайного кода
        expiration_time = datetime.utcnow() + timedelta(minutes=15)  # Код действует 15 минут

        reset_code_entry = await self.user_repo.create_reset_code(
            user_id=user.id,
            reset_code=reset_code,
            expires_at=expiration_time
        )
        
        await self.email_service.send_reset_email(user.email, reset_code)

        return {"detail": "Password reset code has been sent to your email."}

    async def confirm_reset_code(self, data: ResetCodeRequest):
        """
        Подтверждение кода сброса и обновление пароля пользователя.

        :param data: Запрос с кодом сброса и новыми паролями.
        :raises HTTPException: Если код сброса неверный или истек.
        """
        reset_code_entry = await self.user_repo.get_reset_code(data.code)

        if not reset_code_entry:
            raise HTTPException(status_code=404, detail="Invalid or expired reset code")
        
        if reset_code_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Reset code has expired")

        user = await self.user_repo.get_user_by_id(reset_code_entry.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")

        updated_user = await self.user_repo.update_user(user.id, password=data.new_password)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        await self.user_repo.delete_reset_code(data.code)

        return {"detail": "Password has been successfully reset."}
        
    def generate_reset_code(self, length: int = 6) -> str:
        """
        Генерирует случайный код сброса пароля.

        :param length: Длина кода сброса. По умолчанию 6 символов.
        :return: Генерируемый код сброса.
        """
        return ''.join(random.choices(string.digits + string.ascii_letters, k=length))



def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Создает и возвращает сервис пользователя, инкапсулируя все зависимости, включая
    доступ к базе данных и сервис подтверждения email.

    :param db: Асинхронная сессия базы данных, автоматически передаваемая через Depends.
    :return: Экземпляр UserService, готовый к использованию в обработчиках запросов.
    """

    email_service = get_email_service(db)
    user_repo = UserRepository(db)
    
    return UserService(user_repo, email_service)