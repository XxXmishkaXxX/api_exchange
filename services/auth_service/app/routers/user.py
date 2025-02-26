from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.user import ChangePasswordRequest
from app.db.database import get_db
from app.services.auth import oauth2_scheme
from app.services.user import UserService



router = APIRouter()


@router.post("/change-password", response_model=dict)
async def chahge_password(data: ChangePasswordRequest,
                        db: AsyncSession = Depends(get_db),
                        token: str = Security(oauth2_scheme)
                        ):
    service = UserService(db)
    user = await service.get_current_user(token=token)
    await service.change_password(user.id, data)
    return {"message": "Password has changed"}