from uuid import UUID
from fastapi import APIRouter, Depends

from app.deps.security import admin_required
from app.schemas.user import User
from app.services.test_service import Service
from app.deps.services import get_service




router = APIRouter()


@router.delete("/user/{user_id}")
async def delete_user(user_id: UUID, 
                      admin_required = Depends(admin_required), 
                      service: Service = Depends(get_service)) -> User:
    return await service.delete_user(user_id)