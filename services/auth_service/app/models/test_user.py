import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from enum import Enum as PyEnum

class TestRole(str, PyEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserTest(Base):
    """Модель для тестов"""
    __tablename__ = "users_test"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, nullable=False)
    role = Column(Enum(TestRole), default=TestRole.USER)
    api_key = Column(String, nullable=True, unique=True)