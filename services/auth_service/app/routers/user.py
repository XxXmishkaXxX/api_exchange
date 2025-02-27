from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.db.database import get_db
from app.services.auth import oauth2_scheme
from app.services.user import UserService, get_user_service



router = APIRouter()


router = APIRouter()


@router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    data: ChangePasswordRequest,
    service: UserService = Depends(get_user_service),
    token: str = Security(oauth2_scheme)
) -> Dict[str, str]:
    """
    Изменение пароля пользователя.

    :param data: Данные для изменения пароля (ChangePasswordRequest).
    :param service: Сервис для работы с пользователем.
    :param token: Токен доступа для получения текущего пользователя.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок изменения пароля.
    """
    user = await service.get_current_user(token=token)
    return await service.change_password(user.id, data)


@router.post("/forgot-password", response_model=Dict[str, str])
async def forgot_password(
    data: ForgotPasswordRequest, 
    service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """
    Запрос на восстановление пароля.

    :param data: Данные для восстановления пароля (ForgotPasswordRequest).
    :param service: Сервис для работы с пользователем.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок восстановления пароля.
    """
    return await service.forgot_password(data=data)


@router.post("/confirm-reset-code", response_model=Dict[str, str])
async def confirm_reset_code(
    data: ResetCodeRequest, 
    service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """
    Подтверждение кода восстановления пароля.

    :param data: Данные для подтверждения кода восстановления (ResetCodeRequest).
    :param service: Сервис для работы с пользователем.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок подтверждения кода.
    """
    return await service.confirm_reset_code(data=data)


