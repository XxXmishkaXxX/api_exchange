from fastapi import APIRouter, Depends
from app.services.email import EmailService, get_email_service
from app.schemas.email import VerificationRequest, ResendVerificationRequest
from typing import Dict


router = APIRouter()

@router.post("/verify_email", response_model=Dict[str, str])
async def verify_email(
    data: VerificationRequest, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Верификация email пользователя по коду.

    :param data: Данные для верификации email (VerificationRequest).
    :param service: Сервис для работы с верификацией email.
    :return: Ответ в виде словаря с результатом операции.
    """
    return await service.verify_email_code(data)

@router.post("/resend_verification_code", response_model=Dict[str, str])
async def resend_verification_code(
    data: ResendVerificationRequest, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Отправка повторного кода верификации на email.

    :param data: Данные для повторной отправки кода верификации (ResendVerificationRequest).
    :param service: Сервис для повторной отправки кода верификации.
    :return: Ответ в виде словаря с результатом операции.
    """
    return await service.resend_verification_email_code(data)
