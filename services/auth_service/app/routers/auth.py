from fastapi import APIRouter, Depends, Response, Request
from app.services.auth import AuthService, get_auth_service
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from typing import Any


router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> Any:
    """
    Регистрация нового пользователя.

    :param data: Данные для регистрации пользователя (RegisterRequest).
    :param service: Сервис для аутентификации и регистрации пользователей.
    :return: Ответ с результатами регистрации.
    """
    return await service.register_user(data)

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service)) -> Token:
    """
    Аутентификация пользователя.

    :param data: Данные для аутентификации пользователя (LoginRequest).
    :param response: Ответ FastAPI для добавления заголовков и других данных.
    :param service: Сервис для аутентификации пользователей.
    :return: Токен (Token) для авторизованного пользователя.
    """
    return await service.authenticate(data, response)

@router.post("/token/refresh", response_model=Token)
async def refresh(request: Request, service: AuthService = Depends(get_auth_service)) -> Token:
    """
    Обновление токена доступа.

    :param request: Запрос, содержащий данные для обновления токена.
    :param service: Сервис для работы с токенами доступа.
    :return: Новый токен доступа (Token).
    """
    return await service.refresh_access_token(request)
