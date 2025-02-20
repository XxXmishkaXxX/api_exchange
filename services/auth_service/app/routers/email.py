from fastapi import APIRouter, HTTPException, Depends
from app.services.email import VerificationEmailService
from app.db.database import get_db
from app.schemas.email import VerificationRequest, ResendVerificationRequest
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/verify_email", response_model=dict)
async def verify_email(data: VerificationRequest, db: AsyncSession = Depends(get_db)):
    service = VerificationEmailService(db)
    result = await service.verify_email_code(data)
    return result

@router.post("/resend_verification_code", response_model=dict)
async def resend_verification_code(data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    service = VerificationEmailService(db)
    result = await service.resend_verification_email_code(data)
    return result
