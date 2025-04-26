from typing import Any
from fastapi import APIRouter, Depends

from app.services.test_service import Service
from app.deps.services import get_service
from app.schemas.auth import TestRegisterRequest
from app.schemas.user import User


router = APIRouter()


@router.post("/register", response_model=User)
async def register(data: TestRegisterRequest, service: Service = Depends(get_service)) -> User:
    return await service.register_user(data.name)
