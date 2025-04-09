from fastapi import APIRouter, Depends, Response, Request, HTTPException
from typing import Any

from app.services.auth import AuthService, get_auth_service
from app.core.config import oauth
from app.schemas.auth import Token

router = APIRouter()

# === Google OAuth ===
@router.get("/login/google")
async def login_google(request: Request) -> Any:
    """
    Старт процесса аутентификации через Google OAuth.

    :param request: HTTP-запрос.
    :return: Редирект на страницу авторизации Google.
    """
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_google(
    request: Request, 
    response: Response, 
    service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Обработка колбека от Google OAuth после успешной аутентификации.

    :param request: HTTP-запрос, содержащий данные для обработки токена.
    :param response: Ответ для добавления дополнительных данных в ответ.
    :param service: Сервис для аутентификации через OAuth.
    :return: Токен авторизации для пользователя.
    :raises HTTPException: В случае ошибки авторизации Google.
    """
    token = await oauth.google.authorize_access_token(request)
    user_info = token['userinfo']

    if not user_info:
        raise HTTPException(status_code=400, detail="Ошибка авторизации Google")
    
    return await service.oauth_authenticate(user_info=user_info, provider="google", response=response)
