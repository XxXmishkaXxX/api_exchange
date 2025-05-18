import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Role(str, PyEnum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    """Модель для тестов"""
    __tablename__ = "users_test"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
