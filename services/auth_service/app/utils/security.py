from fastapi import HTTPException
from app.tasks.worker_config import app
from starlette.requests import Request
from app.core.config import settings
from app.db.database import redis_client




def check_brute_force(request: Request, action: str):
    """
    Проверяет лимиты попыток для определенного действия (например, вход в систему или сброс пароля).

    - Если количество неудачных попыток превышает допустимый лимит, IP-адрес блокируется на заданное время.
    - Блокировка привязывается к конкретному действию (например, "login", "reset_password").
    - При блокировке отправляется задача в Celery для последующей автоматической разблокировки.

    Args:
        request (Request): Объект HTTP-запроса для получения IP-адреса клиента.
        action (str): Действие, для которого проверяются попытки (например, "login", "reset_password").

    Raises:
        HTTPException: 403 Forbidden, если превышен лимит попыток и IP заблокирован.
    """
    ip = request.client.host
    blocked_key = f"blocked:{action}:{ip}"
    attempts_key = f"attempts:{action}:{ip}"

    if redis_client.exists(blocked_key):
        raise HTTPException(status_code=403, detail="Too many failed attempts. Try again later.")

    attempts = int(redis_client.get(attempts_key) or 0)
    if attempts >= settings.MAX_ATTEMPTS:
        redis_client.setex(blocked_key, settings.BLOCK_TIME, "1")
        app.send_task("app.tasks.tasks.unblock_ip", args=[ip, action]) 
        raise HTTPException(status_code=403, detail="Too many failed attempts. Try again later.")


def record_failed_attempt(request: Request, action: str):
    """
    Записывает неудачную попытку выполнения действия и устанавливает ограничение по времени.

    - Увеличивает счетчик попыток в Redis для указанного действия.
    - Автоматически сбрасывает счетчик через определенное время (BLOCK_TIME).
    - Применяется для предотвращения атак перебора паролей и других злоупотреблений.

    Args:
        request (Request): Объект HTTP-запроса для получения IP-адреса клиента.
        action (str): Действие, для которого фиксируется попытка (например, "login", "reset_password").
    """
    ip = request.client.host
    attempts_key = f"attempts:{action}:{ip}"

    redis_client.incr(attempts_key)
    redis_client.expire(attempts_key, settings.BLOCK_TIME)
