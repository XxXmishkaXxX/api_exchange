from fastapi import APIRouter, Depends, Response, Request
from app.services.auth import AuthService, get_auth_service
from app.schemas.auth import Token, LoginRequest, RegisterRequest


router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    return await service.register_user(data)

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service)):
    return await service.authenticate(data, response)

@router.post("/token/refresh", response_model=Token)
async def refresh(request: Request, service: AuthService = Depends(get_auth_service)):
    return await service.refresh_access_token(request)
