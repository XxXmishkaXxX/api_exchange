from fastapi import Depends, HTTPException, Security
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user_from_token(token: str = Security(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITM_JWT])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="User or role not found in token")
        
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def admin_required(user_info: dict = Depends(get_user_from_token)) -> None:
    if user_info['role'] != "ADMIN":
        raise HTTPException(status_code=403, detail="You do not have permission to access this resource")
