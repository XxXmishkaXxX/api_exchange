from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user_from_token(token: str = Security(oauth2_scheme)):
    """
    Получить информацию о пользователе из токена JWT.

    Аргументы:
        token (str): JWT токен, передаваемый в запросе.

    Возвращает:
        dict: Декодированное содержимое токена (payload).

    Исключения:
        HTTPException: Если токен недействителен или отсутствует.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITM_JWT])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
