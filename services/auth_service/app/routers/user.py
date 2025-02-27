from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.db.database import get_db
from app.services.auth import oauth2_scheme
from app.services.user import UserService, get_user_service



router = APIRouter()


@router.post("/change-password", response_model=dict)
async def chahge_password(data: ChangePasswordRequest,
                        service: UserService = Depends(get_user_service),
                        token: str = Security(oauth2_scheme)
                        ) -> dict:
    
    user = await service.get_current_user(token=token)

    return await service.change_password(user.id, data)


@router.post("/forgot-password", response_model=dict)
async def forgot_password(data: ForgotPasswordRequest, 
                          service: UserService = Depends(get_user_service),
                          ) -> dict:
    return await service.forgot_password(data=data)


@router.post("/confirm-reset-code", response_model=dict)
async def confirm_reset_code(data: ResetCodeRequest, 
                             service: UserService = Depends(get_user_service),
                             ) -> dict:
    return await service.confirm_reset_code(data=data)


