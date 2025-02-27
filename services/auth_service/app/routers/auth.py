from typing import Any
from fastapi import APIRouter, Depends, Response, Request, HTTPException

from app.services.auth import AuthService, get_auth_service
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.utils.security import check_brute_force, record_failed_attempt


router = APIRouter()


@router.post("/register")
async def register(data: RegisterRequest, request: Request, service: AuthService = Depends(get_auth_service)) -> Any:
    """
    Регистрация нового пользователя.

    :param data: Данные для регистрации пользователя (RegisterRequest).
    :param request: Запрос, содержащий IP-адрес пользователя.
    :param service: Сервис для аутентификации и регистрации пользователей.
    :return: Ответ с результатами регистрации.
    """
    check_brute_force(request, "register")

    try:
        return await service.register_user(data)
    except Exception as e:
        record_failed_attempt(request, "register")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, request: Request, response: Response, service: AuthService = Depends(get_auth_service)) -> Token:
    """
    Аутентификация пользователя.

    :param data: Данные для аутентификации пользователя (LoginRequest).
    :param request: Запрос, содержащий IP-адрес пользователя.
    :param response: Ответ FastAPI для добавления заголовков и других данных.
    :param service: Сервис для аутентификации пользователей.
    :return: Токен (Token) для авторизованного пользователя.
    """
    check_brute_force(request, "login")

    try:
        return await service.authenticate(data, response)
    except Exception as e:
        record_failed_attempt(request, "login")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token/refresh", response_model=Token)
async def refresh(request: Request, service: AuthService = Depends(get_auth_service)) -> Token:
    """
    Обновление токена доступа.

    :param request: Запрос, содержащий данные для обновления токена.
    :param service: Сервис для работы с токенами доступа.
    :return: Новый токен доступа (Token).
    """
    check_brute_force(request, "token_refresh")

    try:
        return await service.refresh_access_token(request)
    except Exception as e:
        record_failed_attempt(request, "token_refresh")
        raise HTTPException(status_code=400, detail=str(e))
