from typing import Annotated
from fastapi import APIRouter, Depends, Response, Request, status
from fastapi.responses import JSONResponse

from app.core.limiter import limiter
from app.services.auth import AuthService
from app.services.email import EmailService
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.deps.services import get_auth_service, get_email_service


router = APIRouter()



@router.post("/register")
@limiter.limit("5/10minutes")
async def register(data: RegisterRequest, 
                   request: Request, 
                   auth_service: Annotated[AuthService, Depends(get_auth_service)],
                   email_service: Annotated[EmailService, Depends(get_email_service)]) -> JSONResponse:
    """
    Регистрация нового пользователя.

    :param data: Данные для регистрации пользователя (RegisterRequest).
    :param service: Сервис для аутентификации и регистрации пользователей.
    :return: Ответ с результатами регистрации.
    """
    user = await auth_service.register_user(data)
    await email_service.send_verification_email(user.id, user.email)
    
    return JSONResponse(
        content={"message": "User created successfully", "detail": "verify email"},
        status_code=status.HTTP_201_CREATED
    )


@router.post("/login", response_model=Token)
@limiter.limit("5/10minutes")
async def login(data: LoginRequest, 
                request: Request, 
                response: Response, 
                service: Annotated[AuthService, Depends(get_auth_service)]) -> Token:
    """
    Аутентификация пользователя.

    :param data: Данные для аутентификации пользователя (LoginRequest).
    :param response: Ответ FastAPI для добавления заголовков и других данных.
    :param service: Сервис для аутентификации пользователей.
    :return: Токен (Token) для авторизованного пользователя.
    """
    return await service.authenticate(data, response)


@router.post("/token/refresh", response_model=Token)
@limiter.limit("10/10minutes")
async def refresh(request: Request,
                   service: Annotated[AuthService, Depends(get_auth_service)]) -> Token:
    """
    Обновление токена доступа.

    :param request: Запрос, содержащий данные для обновления токена.
    :param service: Сервис для работы с токенами доступа.
    :return: Новый токен доступа (Token).
    """
    return await service.refresh_access_token(request)
