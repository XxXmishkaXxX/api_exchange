from fastapi import APIRouter, Depends
from app.services.email import VerificationEmailService, get_email_service
from app.schemas.email import VerificationRequest, ResendVerificationRequest


router = APIRouter()

@router.post("/verify_email", response_model=dict)
async def verify_email(data: VerificationRequest, 
                       service: VerificationEmailService = Depends(get_email_service)
                       ) -> dict:
    return await service.verify_email_code(data)

@router.post("/resend_verification_code", response_model=dict)
async def resend_verification_code(data: ResendVerificationRequest, 
                                   service: VerificationEmailService = Depends(get_email_service)
                                   ) -> dict:
    return await service.resend_verification_email_code(data)
