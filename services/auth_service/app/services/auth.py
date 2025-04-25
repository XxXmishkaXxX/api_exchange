import jwt
from fastapi import HTTPException, Response, Request, status
from datetime import datetime, timedelta
from uuid import UUID


from app.models.user import User, Role
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.core.config import settings


class AuthService:
    """Сервис аутентификации и авторизации пользователей."""

    def __init__(self, user_repo: UserRepository) -> None:
        """Инициализация сервиса с настройками шифрования паролей."""
        self.user_repo = user_repo

    async def register_user(self, data: RegisterRequest) -> User:
        """Регистрирует нового пользователя.
        
        Args:
            data (RegisterRequest): Данные для регистрации пользователя.
        
        Returns:
            tuple[dict[str, str], int]: Сообщение о создании пользователя и HTTP статус.
        """
        
        if await self.user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")

        user = User(
            email=data.email,
            name=data.name,
            password=self.user_repo.get_password_hash(data.password),
        )
        
        user = await self.user_repo.create(user)

        return user

    async def register_admin(self, data: RegisterRequest):
        
        if await self.user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")
        
        user = User(
            email=data.email,
            name=data.name,
            password=self.user_repo.get_password_hash(data.password),
            role=Role.ADMIN,
            is_verified=True
        )

        user = await self.user_repo.create(user)

        return {"message": "Admin created successfully"}, status.HTTP_201_CREATED
        

    async def authenticate(self, data: LoginRequest, response: Response) -> Token:
        """Аутентифицирует пользователя по email и паролю.
        
        Args:
            data (LoginRequest): Данные для входа (email и пароль).
            response (Response): Объект ответа для установки cookies.
        
        Returns:
            Token: Сгенерированный access token.
        """
        user = await self.user_repo.get_user_by_email(data.email)
        
        if not user or await self.user_repo.verify_password(data.password, user.password) is False:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="User is not verified")

        return await self._generate_tokens(user.id, user.role, response)

    async def oauth_authenticate(self, user_info: dict[str, str], provider: str, response: Response) -> Token:
        """Аутентифицирует пользователя через OAuth-провайдера.
        
        Args:
            user_info (dict[str, str]): Данные пользователя от OAuth.
            provider (str): Название провайдера.
            response (Response): Объект ответа для установки cookies.
        
        Returns:
            Token: Сгенерированный access token.
        """
        oauth_id, email = str(user_info.get("sub")), user_info.get("email")

        user = await self.user_repo.get_user_by_email(email)

        if not user:
            user = User(
                email=email,
                name=user_info.get("name", "No Name"),
                oauth_provider=provider,
                oauth_id=oauth_id,
                is_verified=True
            )
            await self.user_repo.create(user)

        return await self._generate_tokens(user.id, user.role, response)

    async def refresh_access_token(self, request: Request) -> Token:
        """Обновляет access token по refresh token.
        
        Args:
            request (Request): Запрос с cookies.
        
        Returns:
            Token: Новый access token.
        """
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        user_id = await self._decode_jwt(refresh_token)
        return Token(access_token=await self._generate_jwt(user_id, days=1))

    async def _generate_tokens(self, user_id: UUID, role: str, response: Response) -> Token:
        access_token = await self._generate_jwt(user_id, role, days=1)
        refresh_token = await self._generate_jwt(user_id, role, days=100)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            samesite="Lax",
            max_age=100 * 24 * 60 * 60,
        )
        return Token(access_token=access_token)

    async def _generate_jwt(self, user_id: UUID, role: str, minutes: int = 0, days: int = 0) -> str:
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode(
            {"sub": str(user_id), "role": role, "exp": expire},
            settings.SECRET_KEY,
            algorithm="HS256"
        )

    async def _decode_jwt(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            id = payload.get("sub")
            if not id:
                raise HTTPException(status_code=401, detail="Invalid token")
            return UUID(id)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")