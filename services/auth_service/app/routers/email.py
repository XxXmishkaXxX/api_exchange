from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Dict

from app.services.email import EmailService, get_email_service
from app.schemas.email import VerificationRequest, ResendVerificationRequest
from app.utils.security import check_brute_force, record_failed_attempt


router = APIRouter()


@router.post("/verify_email", response_model=Dict[str, str])
async def verify_email(
    request: Request,
    data: VerificationRequest, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Верификация email пользователя по коду.

    - Ограничение количества попыток для предотвращения атак перебора.
    - Блокировка IP при превышении лимита неудачных попыток.

    :param request: Объект запроса для получения IP-адреса пользователя.
    :param data: Данные для верификации email (VerificationRequest).
    :param service: Сервис для работы с верификацией email.
    :return: Ответ в виде словаря с результатом операции.
    """
    check_brute_force(request, "verify_email")

    try:
        return await service.verify_email_code(data)
    except Exception as e:
        record_failed_attempt(request, "verify_email")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resend_verification_code", response_model=Dict[str, str])
async def resend_verification_code(
    request: Request,
    data: ResendVerificationRequest, 
    service: EmailService = Depends(get_email_service)
) -> Dict[str, str]:
    """
    Отправка повторного кода верификации на email.

    - Ограничение количества запросов для предотвращения злоупотреблений.
    - Блокировка IP при слишком частых запросах.

    :param request: Объект запроса для получения IP-адреса пользователя.
    :param data: Данные для повторной отправки кода верификации (ResendVerificationRequest).
    :param service: Сервис для повторной отправки кода верификации.
    :return: Ответ в виде словаря с результатом операции.
    """

    check_brute_force(request, "resend_verification_code")

    try:
        return await service.resend_verification_email_code(data)
    except Exception as e:
        record_failed_attempt(request, "resend_verification_code")
        raise HTTPException(status_code=400, detail=str(e))
