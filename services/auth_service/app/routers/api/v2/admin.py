from typing import Any, Annotated
from fastapi import APIRouter, Depends, Request 
from uuid import UUID
from app.core.limiter import limiter
from app.services.auth import AuthService
from app.schemas.auth import RegisterRequest
from app.services.user import UserService
from app.deps.services import get_auth_service, get_user_service
from app.deps.security import admin_required
from app.schemas.user import User

router = APIRouter()

@router.post("/register/admin")
async def register_admin(data: RegisterRequest, 
                         request: Request, 
                         service: Annotated[AuthService, Depends(get_auth_service)],
                         user_info: Annotated[dict, Depends(admin_required)]) -> Any:
    """
    Регистрация администратора. Доступно только другим администраторам.

    :param data: Данные для регистрации пользователя (RegisterRequest).
    :param service: Сервис для аутентификации и регистрации пользователей.
    :param user_info: Проверка токена на роль администратора.
    :return: Ответ с результатами регистрации.
    """
    return await service.register_admin(data)

@router.delete("/user/{user_id}")
async def delete_user(user_id: UUID, 
                      admin_required: Annotated[None, Depends(admin_required)], 
                      service: Annotated[UserService, Depends(get_user_service)]) -> User:
    return await service.delete_user(user_id)