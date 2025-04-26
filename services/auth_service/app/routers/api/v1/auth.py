from typing import Any
from fastapi import APIRouter, Depends

from app.services.test_service import Service
from app.deps.services import get_service
from app.schemas.auth import TestRegisterRequest


router = APIRouter()


@router.post("/register")
async def register(data: TestRegisterRequest, service: Service = Depends(get_service)) -> Any:
    return await service.register_user(data.name)
