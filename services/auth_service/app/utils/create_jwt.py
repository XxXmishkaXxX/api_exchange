import jwt
from datetime import datetime, timedelta
from uuid import UUID

from app.core.config import settings


def create_api_key(user_id: UUID, role: str, minutes: int = 0, days: int = 365):
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode(
            {"sub": str(user_id), "role": role, "exp": expire},
            settings.SECRET_KEY,
            algorithm="HS256"
        )
