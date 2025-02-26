from pydantic import BaseModel, EmailStr

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    new_password_confirm: str
    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetCodeRequest(BaseModel):
    code: str
    new_password: str
    new_password_confirm: str