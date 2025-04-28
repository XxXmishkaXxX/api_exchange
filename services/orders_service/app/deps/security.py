from fastapi import HTTPException, Header, Depends
import jwt
from uuid import UUID
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError
from typing import Optional

from app.core.config import settings



def get_token(authorization: Optional[str] = Header(None)) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    
    if not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=400, detail="Invalid token format. Expected 'TOKEN <your-token>'")
    
    token = authorization[len("TOKEN "):]
    return token

def get_user_from_token(token: str = Depends(get_token)) -> UUID:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITM])
        user_id: UUID = UUID(payload.get("sub"))
        role: str = payload.get("role")
        
        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return user_id
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
