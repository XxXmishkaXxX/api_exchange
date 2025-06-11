import asyncio
from uuid import UUID

from fastapi import HTTPException

from app.repositories.user_repo import UserRepository
from app.schemas.user import User as UserSchema
from app.models.user import User
from app.models.user import Role
from app.kafka.producers.send_user_event_producer import SendUserEventProducerService
from app.utils.create_jwt import create_api_key

class AuthService:

    def __init__(self, repo: UserRepository, prod: SendUserEventProducerService) -> None:
        self.repo = repo
        self.prod = prod

    async def register_user(self, name: str) -> UserSchema:  
        
        user = User(
            name=name,
            role=Role.USER,
        )
        
        user = await self.repo.create(user)

        api_key = create_api_key(user_id=user.id, role=user.role)

        user.api_key = api_key

        user = await self.repo.update_user(user)

        await self.prod.send_event(user_id=user.id, event="create")

        return UserSchema(id=user.id, name=user.name, role=user.role, api_key=user.api_key)
    
    async def delete_user(self, user_id: UUID) -> UserSchema:

        user = await self.repo.delete_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User was not found")
        
        await self.prod.send_event(user_id=user.id, event="delete")

        asyncio.sleep(0.8)

        return UserSchema(id=user.id, name=user.name, role=user.role, api_key=user.api_key)
