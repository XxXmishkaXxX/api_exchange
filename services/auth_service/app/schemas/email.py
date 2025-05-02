from typing import Annotated
from pydantic import BaseModel, EmailStr, Field

class VerificationRequest(BaseModel):
    email: Annotated[EmailStr, Field()]
    verification_code: Annotated[str, Field()]

class ResendVerificationRequest(BaseModel):
    email: Annotated[EmailStr, Field()]
