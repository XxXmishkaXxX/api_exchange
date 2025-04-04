from fastapi import Depends, HTTPException, Security
import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_user_from_token(token: str = Security(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return {"user_id": int(user_id), "role": role}
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(user_info: dict = Depends(get_user_from_token)) -> None:
    if user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to access this resource")
