from pydantic import BaseModel, EmailStr

class VerificationRequest(BaseModel):
    email: EmailStr 
    verification_code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr