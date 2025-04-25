import random
import string
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException

from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetCodeRequest
from app.schemas.user import User


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_user(self, user_id: UUID = None, user_email: str = None):
        user = None
        if user_id:
            user = await self.user_repo.get_user_by_id(user_id)
        if user_email:
            user = await self.user_repo.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user

    async def delete_user(self, user_id: UUID) -> User:
        user = await self.user_repo.delete_user(user_id)
        return User(user_id=user.id, name=user.name, role=user.role)
    
    async def verify_user(self, user_email: str):
        user = await self.get_user(user_email=user_email)
        user.is_verified = True
        await self.user_repo.update_user(user)

    async def change_password(self, user_id: UUID, data: ChangePasswordRequest) -> dict:
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not await self.user_repo.verify_password(data.old_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect old password")
        
        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")

        user.password = self.user_repo.get_password_hash(data.new_password)

        updated_user = await self.user_repo.update_user(user)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        return {"message": "Password has changed"}

    async def forgot_password(self, data: ForgotPasswordRequest):
        user = await self.user_repo.get_user_by_email(data.email)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        reset_code = self.generate_reset_code()
        expiration_time = datetime.utcnow() + timedelta(minutes=15)

        reset_code_entry = await self.user_repo.create_reset_code(
            user_id=user.id,
            reset_code=reset_code,
            expires_at=expiration_time
        )
        return reset_code_entry

    async def confirm_reset_code(self, data: ResetCodeRequest):
        reset_code_entry = await self.user_repo.get_reset_code(data.code)

        if not reset_code_entry:
            raise HTTPException(status_code=404, detail="Invalid or expired reset code")
        
        if reset_code_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Reset code has expired")

        user = await self.user_repo.get_user_by_id(reset_code_entry.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if data.new_password != data.new_password_confirm:
            raise HTTPException(status_code=400, detail="Passwords don't match")

        user.password = self.user_repo.get_password_hash(data.new_password)

        updated_user = await self.user_repo.update_user(user)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to update password")
        
        await self.user_repo.delete_reset_code(data.code)

        return {"detail": "Password has been successfully reset."}

    def generate_reset_code(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits + string.ascii_letters, k=length))
