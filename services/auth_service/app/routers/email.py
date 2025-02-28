from fastapi import APIRouter, Depends, Request
from typing import Dict

from app.services.email import EmailService, get_email_service
from app.schemas.email import VerificationRequest, ResendVerificationRequest
from app.core.limiter import limiter

router = APIRouter()


@router.post("/verify_email", response_model=Dict[str, str])
@limiter.limit("3/15minutes")
async def verify_email(
    request: Request,
    data: VerificationRequest, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Верификация email пользователя по коду.

    - Ограничение количества попыток для предотвращения атак перебора.

    :param data: Данные для верификации email (VerificationRequest).
    :param service: Сервис для работы с верификацией email.
    :return: Ответ в виде словаря с результатом операции.
    """
    return await service.verify_email_code(data)



@router.post("/resend_verification_code", response_model=Dict[str, str])
@limiter.limit("3/15minutes")
async def resend_verification_code(
    data: ResendVerificationRequest,
    request: Request, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Отправка повторного кода верификации на email.

    - Ограничение количества запросов для предотвращения злоупотреблений.

    :param data: Данные для повторной отправки кода верификации (ResendVerificationRequest).
    :param service: Сервис для повторной отправки кода верификации.
    :return: Ответ в виде словаря с результатом операции.
    """
    return await service.resend_verification_email_code(data)

