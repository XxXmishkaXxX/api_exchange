from typing import Dict
from fastapi import APIRouter, Depends, Security, Request

from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.services.user import UserService, get_user_service
from app.core.limiter import limiter
from app.deps.security import get_user_from_token



router = APIRouter()


@router.post("/change-password", response_model=Dict[str, str])
@limiter.limit("3/10minutes")
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    user_info: dict = Depends(get_user_from_token) 
) -> Dict[str, str]:
    """
    Изменение пароля пользователя.

    :param data: Данные для изменения пароля (ChangePasswordRequest).
    :param service: Сервис для работы с пользователем.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок изменения пароля.
    """
    return await service.change_password(user_info["user_id"], data)


@router.post("/forgot-password", response_model=Dict[str, str])
@limiter.limit("3/15minutes")
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
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
@limiter.limit("3/15minutes")
async def confirm_reset_code(
    data: ResetCodeRequest,
    request: Request,
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


