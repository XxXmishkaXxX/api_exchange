from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Security, Request


from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.services.auth import oauth2_scheme
from app.services.user import UserService, get_user_service
from app.utils.security import check_brute_force, record_failed_attempt



router = APIRouter()


@router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    token: str = Security(oauth2_scheme)
) -> Dict[str, str]:
    """
    Изменение пароля пользователя.

    :param data: Данные для изменения пароля (ChangePasswordRequest).
    :param request: Запрос, содержащий IP-адрес пользователя.
    :param service: Сервис для работы с пользователем.
    :param token: Токен доступа для получения текущего пользователя.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок изменения пароля.
    """
    check_brute_force(request, "change_password")

    try:
        user = await service.get_current_user(token=token)
        return await service.change_password(user.id, data)
    except Exception as e:
        record_failed_attempt(request, "change_password")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot-password", response_model=Dict[str, str])
async def forgot_password(
    data: ForgotPasswordRequest, 
    request: Request,
    service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """
    Запрос на восстановление пароля.

    :param data: Данные для восстановления пароля (ForgotPasswordRequest).
    :param request: Запрос, содержащий IP-адрес пользователя.
    :param service: Сервис для работы с пользователем.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок восстановления пароля.
    """
    check_brute_force(request, "forgot_password")

    try:
        return await service.forgot_password(data=data)
    except Exception as e:
        record_failed_attempt(request, "forgot_password")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm-reset-code", response_model=Dict[str, str])
async def confirm_reset_code(
    data: ResetCodeRequest, 
    request: Request,
    service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """
    Подтверждение кода восстановления пароля.

    :param data: Данные для подтверждения кода восстановления (ResetCodeRequest).
    :param request: Запрос, содержащий IP-адрес пользователя.
    :param service: Сервис для работы с пользователем.
    :return: Ответ с результатом операции (словарь с сообщением).
    :raises HTTPException: В случае ошибок подтверждения кода.
    """
    check_brute_force(request, "confirm_reset_code")

    try:
        return await service.confirm_reset_code(data=data)
    except Exception as e:
        record_failed_attempt(request, "confirm_reset_code")
        raise HTTPException(status_code=400, detail=str(e))


