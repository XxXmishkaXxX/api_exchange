from pydantic import BaseModel, EmailStr, Field, model_validator
import re

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str

    @model_validator(mode="before")
    def validate_passwords_before(cls, values: dict) -> dict:
        new_password = values.get("new_password")
        new_password_confirm = values.get("new_password_confirm")
        
        # Проверка совпадения паролей
        if new_password != new_password_confirm:
            raise ValueError("Пароли не совпадают.")
        
        # Дополнительная проверка пароля
        if new_password and not re.search(r"[a-z]", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if new_password and not re.search(r"[A-Z]", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if new_password and not re.search(r"\d", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        if new_password and not re.search(r"[@$!%*?&]", new_password):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (@$!%*?&).")
        
        return values

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetCodeRequest(BaseModel):
    code: str
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str

    @model_validator(mode="before")
    def validate_passwords_before(cls, values: dict) -> dict:
        new_password = values.get("new_password")
        new_password_confirm = values.get("new_password_confirm")
        
        # Проверка совпадения паролей
        if new_password != new_password_confirm:
            raise ValueError("Пароли не совпадают.")
        
        # Дополнительная проверка пароля
        if new_password and not re.search(r"[a-z]", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву.")
        if new_password and not re.search(r"[A-Z]", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву.")
        if new_password and not re.search(r"\d", new_password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру.")
        if new_password and not re.search(r"[@$!%*?&]", new_password):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (@$!%*?&).")
        
        return values
