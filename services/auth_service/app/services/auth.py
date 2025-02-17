import jwt
from fastapi import HTTPException, Response, Request, status
from passlib.context import CryptContext
from datetime import datetime, timedelta

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.core.config import settings


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def register_user(self, data: RegisterRequest, db):
        user_repo = UserRepository(db)
        if user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")
        
        user = User(
            email=data.email,
            name=data.name,
            password=self.pwd_context.hash(data.password),
        )
        user_repo.create(user)
        return {"message": "User created successfully"}, status.HTTP_201_CREATED

    def authenticate(self, data: LoginRequest, db, response: Response):
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_email(data.email)
        if not user or not user_repo.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return self._generate_tokens(user.email, response)

    def oauth_authenticate(self, user_info: dict, provider: str, db, response: Response):
        oauth_id, email = str(user_info.get("id")), user_info.get("email")
        user = db.query(User).filter(
            (User.oauth_id == oauth_id) & (User.oauth_provider == provider)
        ).first() or (db.query(User).filter(User.email == email).first() if email else None)
        
        if not user:
            user = User(
                email=email,
                name=user_info.get("name", "No Name"),
                oauth_provider=provider,
                oauth_id=oauth_id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return self._generate_tokens(user.email, response)

    def refresh_access_token(self, request: Request):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")
        
        email = self._decode_jwt(refresh_token)
        return Token(access_token=self._generate_jwt(email, days=1))

    def _generate_tokens(self, email: str, response: Response):
        access_token = self._generate_jwt(email, days=1)
        refresh_token = self._generate_jwt(email, days=100)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            samesite="Lax",
            max_age=100 * 24 * 60 * 60,
        )
        return Token(access_token=access_token)

    def _generate_jwt(self, email: str, minutes: int = 0, days: int = 0) -> str:
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode({"sub": email, "exp": expire}, settings.SECRET_KEY, algorithm="HS256")

    def _decode_jwt(self, token: str) -> str:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token")
            return email
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
