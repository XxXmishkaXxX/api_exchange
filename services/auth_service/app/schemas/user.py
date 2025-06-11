import re
from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, Field


UUIDField = Annotated[UUID, Field()]
StringField = Annotated[str, Field()]


class User(BaseModel):
    """Схема пользователя"""
    id: UUIDField
    name: StringField
    role: StringField
    api_key: StringField
