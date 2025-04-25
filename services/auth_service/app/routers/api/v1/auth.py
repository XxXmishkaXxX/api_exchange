from typing import Any
from fastapi import APIRouter, Depends, Response, Request

from app.core.limiter import limiter
from app.services.auth import AuthService
from app.deps.services import get_auth_service


router = APIRouter()


@router.post("/register")
async def register(name: str , request: Request, service: AuthService = Depends(get_auth_service)) -> Any:
    """
    Регистрация нового пользователя.

    :param name: Имя пользователя
    :param service: Сервис для аутентификации и регистрации пользователей.
    :return: Ответ с результатами регистрации.
    """
    pass
