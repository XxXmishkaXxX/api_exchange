import jwt
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException

from app.repositories.test_repo import TestUserRepository
from app.schemas.user import User
from app.models.test_user import UserTest
from app.models.test_user import TestRole
from app.core.config import settings
from app.kafka.producers.send_wallet_event_producer import SendWalletEventProducerService

class Service:
    """Сервис для тестов"""

    def __init__(self, repo: TestUserRepository, prod: SendWalletEventProducerService) -> None:
        self.repo = repo
        self.prod = prod

    async def register_user(self, name: str) -> User:  
        
        user = UserTest(
            name=name,
            role=TestRole.USER,
        )
        
        user = await self.repo.create(user)

        api_key = await self.create_api_key(user_id=user.id, role=user.role)

        user.api_key = api_key

        user = await self.repo.update_user(user)

        await self.prod.send_event(user_id=user.id, event="create")

        return User(user_id=user.id, name=user.name, role=user.role, api_key=user.api_key)
    
    async def delete_user(self, user_id: UUID):

        user = await self.repo.delete_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User was not found")
        
        await self.prod.send_event(user_id=user.id, event="delete")

        return User(user_id=user.id, name=user.name, role=user.role, api_key=user.api_key)

    async def create_api_key(self, user_id: UUID, role: str, minutes: int = 0, days: int = 365):
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode(
            {"sub": str(user_id), "role": role, "exp": expire},
            settings.SECRET_KEY,
            algorithm="HS256"
        )
