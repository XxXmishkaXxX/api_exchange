from fastapi import APIRouter, HTTPException, Depends
from app.services.email import VerificationEmailService
from app.db.database import get_db
from app.schemas.email import VerificationRequest

router = APIRouter()

@router.post("/verify_email", response_model=dict)
async def verify_email(data: VerificationRequest, service: VerificationEmailService = Depends(get_db)):
    return await service.verify_email_code(data)


# @router.post("/resend_verification_code", response_model=dict)
# async def resend_verification_code(
#     resend_request: ResendVerificationRequest,
#     user_repo: UserRepository = Depends(get_db),  # Получаем репозиторий через зависимость
#     verification_service: VerificationEmail = Depends(VerificationEmail),
# ):
#     """
#     Повторная отправка кода подтверждения на почту.
#     """
#     try:
#         result = await verification_service.resend_verification_email_code(resend_request.user_id)
#         return result
#     except HTTPException as e:
#         raise e