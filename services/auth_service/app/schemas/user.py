import re
from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, model_validator


UUIDField = Annotated[UUID, Field()]
StringField = Annotated[str, Field()]
PasswordField = Annotated[str, Field(min_length=8, max_length=128)]
EmailField = Annotated[EmailStr, Field()]


class PasswordValidationMixin(BaseModel):
    new_password: PasswordField
    new_password_confirm: StringField

    @model_validator(mode="before")
    def validate_passwords(cls, values: dict) -> dict:
        new_password = values.get("new_password")
        confirm_password = values.get("new_password_confirm")
        
        if new_password != confirm_password:
            raise ValueError("Пароли не совпадают.")

        password_checks = [
            (r"[a-z]", "Пароль должен содержать хотя бы одну строчную букву."),
            (r"[A-Z]", "Пароль должен содержать хотя бы одну заглавную букву."),
            (r"\d", "Пароль должен содержать хотя бы одну цифру."),
            (r"[@$!%*?&]", "Пароль должен содержать хотя бы один специальный символ (@$!%*?&)."),
        ]

        for pattern, message in password_checks:
            if not re.search(pattern, new_password or ""):
                raise ValueError(message)

        return values


class User(BaseModel):
    """Схема пользователя для тестов"""
    user_id: UUIDField
    name: StringField
    role: StringField
    api_key: StringField

class ChangePasswordRequest(PasswordValidationMixin):
    old_password: PasswordField

class ForgotPasswordRequest(BaseModel):
    email: EmailField

class ResetCodeRequest(PasswordValidationMixin):
    code: StringField
