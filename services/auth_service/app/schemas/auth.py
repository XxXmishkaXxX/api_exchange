import re
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, field_validator

class TestRegisterRequest(BaseModel):
    name: Annotated[str, Field()]

class RegisterRequest(BaseModel):
    email: Annotated[EmailStr, Field()]
    name: Annotated[
        str,
        Field(min_length=2, max_length=50, pattern=r"^[A-Za-zА-Яа-яЁё]+$")
    ]
    password: Annotated[
        str,
        Field(min_length=8, max_length=128)
    ]

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r"[@$!%*?&]", value):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (@$!%*?&).")
        return value

class LoginRequest(BaseModel):
    email: Annotated[EmailStr, Field()]
    password: Annotated[
        str,
        Field(min_length=8, max_length=128)
    ]

class Token(BaseModel):
    access_token: Annotated[str, Field()]
