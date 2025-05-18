from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.auth import AuthService
from app.kafka.producers.send_user_event_producer import get_user_event_producer, SendUserEventProducerService

from app.repositories.user_repo import UserRepository


def get_service(db: AsyncSession = Depends(get_db),
                prod: SendUserEventProducerService = Depends(get_user_event_producer)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo, prod)