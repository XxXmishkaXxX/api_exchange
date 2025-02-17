import jwt
from fastapi import HTTPException, Response, Request,status
from passlib.context import CryptContext
from datetime import datetime, timedelta

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.core.config import settings


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # 🔹 Регистрация (email + пароль)
    def register_user(self, data: RegisterRequest, db):
        user_repo = UserRepository(db)
        
        # Проверка, существует ли уже пользователь
        if user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")

        # Хешируем пароль и создаем пользователя
        hashed_password = self.pwd_context.hash(data.password)
        user = User(email=data.email, name=data.name, password=hashed_password)
        user_repo.create(user)

        return {"message": "User created successfully"}, status.HTTP_201_CREATED

    # 🔹 Аутентификация (email + пароль)
    def authenticate(self, data: LoginRequest, db, response: Response):
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_email(data.email)
        
        # Проверка на существование пользователя и совпадение пароля
        if not user or not user_repo.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Генерация access и refresh токенов
        access_token = self._generate_jwt(user.email, days=1)
        refresh_token = self._generate_jwt(user.email, days=100)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            samesite="Lax",
            max_age=100 * 24 * 60 * 60  # 100 дней
        )

        return Token(access_token=access_token)
    
    def oauth_authenticate(self, user_info: dict, provider: str, db, response):
        oauth_id = str(user_info.get("id"))  # ID из Google или VK
        email = user_info.get("email")  # Может быть None

        # Ищем пользователя по oauth_id
        user = db.query(User).filter(User.oauth_id == oauth_id, User.oauth_provider == provider).first()

        if not user and email:
            # Если пользователя нет, но есть email, проверяем email
            user = db.query(User).filter(User.email == email).first()

        if not user:
            # Создаём нового пользователя
            user = User(
                email=email,
                name=user_info.get("name", "No Name"),
                oauth_provider=provider,
                oauth_id=oauth_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        access_token = self._generate_jwt(user.email, days=1)
        refresh_token = self._generate_jwt(user.email, days=100)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            samesite="Lax",
            max_age=100 * 24 * 60 * 60  # 100 дней
        )

        return Token(access_token=access_token)

    def refresh_access_token(self, request: Request):
        
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        try:
        
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")
            
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = self._generate_jwt(email, days=1)

        return Token(access_token=access_token)

    # 🔹 Генерация JWT токенов
    def _generate_jwt(self, email: str, minutes: int = 0, days: int = 0):
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        payload = {"sub": email, "exp": expire}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
