from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends

from app.deps.security import admin_required
from app.schemas.user import User
from app.services.auth import AuthService
from app.deps.services import get_service




router = APIRouter()


@router.delete("/user/{user_id}", response_model=User)
async def delete_user(user_id: UUID, 
                      admin_required: Annotated[None, Depends(admin_required)], 
                      service: Annotated[AuthService, Depends(get_service)]) -> User:
    return await service.delete_user(user_id)