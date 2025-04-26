from pydantic import BaseModel, EmailStr, Field, field_validator
import re


from pydantic import BaseModel

class TestRegisterRequest(BaseModel):
    name: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50, pattern=r"^[A-Za-zА-Яа-яЁё]+$")
    password: str = Field(..., min_length=8, max_length=128)

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
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class Token(BaseModel):
    access_token: str
