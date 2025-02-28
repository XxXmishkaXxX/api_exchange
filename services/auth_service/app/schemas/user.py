from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str

    @field_validator("new_password")
    def validate_new_password(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r"[@$!%*?&]", value):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (@$!%*?&).")
        return value

    @field_validator("new_password_confirm")
    def validate_new_password_confirm(cls, value: str, values: dict) -> str:
        if "new_password" in values and value != values["new_password"]:
            raise ValueError("Пароли не совпадают.")
        return value

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetCodeRequest(BaseModel):
    code: str
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str

    @field_validator("new_password")
    def validate_new_password(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r"[@$!%*?&]", value):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (@$!%*?&).")
        return value

    @field_validator("new_password_confirm")
    def validate_new_password_confirm(cls, value: str, values: dict) -> str:
        if "new_password" in values and value != values["new_password"]:
            raise ValueError("Пароли не совпадают.")
        return value
