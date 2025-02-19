from fastapi import APIRouter, Depends, Response, Request
from app.services.auth import AuthService
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest, service: AuthService = Depends(), db: AsyncSession = Depends(get_db)):
    return await service.register_user(data, db)

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, response: Response, service: AuthService = Depends(), db: AsyncSession = Depends(get_db)):
    return await service.authenticate(data, db, response)

@router.post("/token/refresh", response_model=Token)
async def refresh(request: Request, service: AuthService = Depends()):
    return await service.refresh_access_token(request)
