from typing import Annotated
from fastapi import APIRouter, Depends

from app.services.auth import AuthService
from app.deps.services import get_service
from app.schemas.auth import RegisterRequest
from app.schemas.user import User


router = APIRouter()


@router.post("/register", response_model=User)
async def register(data: RegisterRequest, 
                   service: Annotated[AuthService, Depends(get_service)]) -> User:
    return await service.register_user(data.name)
