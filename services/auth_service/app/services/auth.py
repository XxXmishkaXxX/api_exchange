import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.core.config import settings

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # 🔹 Регистрация (email + пароль)
    def register_user(self, data: RegisterRequest, db):
        user_repo = UserRepository(db)
        if user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = self.pwd_context.hash(data.password)
        user = User(email=data.email, name=data.name, password=hashed_password)
        user_repo.create(user)

        token = self._generate_jwt(user.email)
        return Token(access_token=token)

    # 🔹 Логин (email + пароль)
    def authenticate(self, data: LoginRequest, db):
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_email(data.email)
        
        if not user or not user_repo.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = self._generate_jwt(user.email)
        return Token(access_token=token)

    def _generate_jwt(self, email: str):
        return jwt.encode({"sub": email}, settings.SECRET_KEY, algorithm="HS256")
