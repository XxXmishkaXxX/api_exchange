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

    def _get_user_repo(self, db):
        return UserRepository(db)

    async def register_user(self, data: RegisterRequest, db):
        user_repo = self._get_user_repo(db)
        if await user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")
        
        user = User(
            email=data.email,
            name=data.name,
            password=self.pwd_context.hash(data.password),
        )
        await user_repo.create(user)
        return {"message": "User created successfully", 
                "detail":"verify email"}, status.HTTP_201_CREATED

    async def authenticate(self, data: LoginRequest, db, response: Response):
        user_repo = self._get_user_repo(db)
        user = await user_repo.get_user_by_email(data.email)
        
        if not user or not user_repo.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="User is not verified")
        
        return await self._generate_tokens(user.email, response)

    async def oauth_authenticate(self, user_info: dict, provider: str, db, response: Response):
        oauth_id, email = str(user_info.get("sub")), user_info.get("email")
        
        user_repo = self._get_user_repo(db)
        user = await user_repo.get_user_by_email(email)

        if not user:
            user = User(
                email=email,
                name=user_info.get("name", "No Name"),
                oauth_provider=provider,
                oauth_id=oauth_id,
                is_verified=True
            )
            await user_repo.create(user)

        return await self._generate_tokens(user.email, response)

    async def refresh_access_token(self, request: Request):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")
        
        email = await self._decode_jwt(refresh_token)
        return Token(access_token=await self._generate_jwt(email, days=1))

    async def _generate_tokens(self, email: str, response: Response):
        access_token = await self._generate_jwt(email, days=1)
        refresh_token = await self._generate_jwt(email, days=100)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            samesite="Lax",
            max_age=100 * 24 * 60 * 60,
        )
        return Token(access_token=access_token)

    async def _generate_jwt(self, email: str, minutes: int = 0, days: int = 0) -> str:
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode({"sub": email, "exp": expire}, settings.SECRET_KEY, algorithm="HS256")

    async def _decode_jwt(self, token: str) -> str:
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
