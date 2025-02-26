import jwt
from fastapi import HTTPException, Response, Request, status, Depends
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer


from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.email import VerificationEmailService
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.core.config import settings
from app.db.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


class AuthService:
    """Сервис аутентификации и авторизации пользователей."""

    def __init__(self, user_repo: UserRepository, email_service: VerificationEmailService) -> None:
        """Инициализация сервиса с настройками шифрования паролей."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.user_repo = user_repo
        self.email_service = email_service

    async def register_user(self, data: RegisterRequest) -> tuple[dict[str, str], int]:
        """Регистрирует нового пользователя.
        
        Args:
            data (RegisterRequest): Данные для регистрации пользователя.
            db (AsyncSession): Сессия базы данных.

        Returns:
            tuple[dict[str, str], int]: Сообщение о создании пользователя и HTTP статус.
        """
        
        if await self.user_repo.get_user_by_email(data.email):
            raise HTTPException(status_code=400, detail="User already exists")

        user = User(
            email=data.email,
            name=data.name,
            password=self.pwd_context.hash(data.password),
        )
        
        user = await self.user_repo.create(user)
        await self.email_service.send_verification_email(user.id, user.email)

        return {"message": "User created successfully", "detail": "verify email"}, status.HTTP_201_CREATED

    async def authenticate(self, data: LoginRequest, response: Response) -> Token:
        """Аутентифицирует пользователя по email и паролю.
        
        Args:
            data (LoginRequest): Данные для входа (email и пароль).
            db (AsyncSession): Сессия базы данных.
            response (Response): Объект ответа для установки cookies.

        Returns:
            Token: Сгенерированный access token.
        """

        user = await self.user_repo.get_user_by_email(data.email)

        if not user or not self.user_repo.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="User is not verified")

        return await self._generate_tokens(user.email, response)

    async def oauth_authenticate(self, user_info: dict[str, str], provider: str, response: Response) -> Token:
        """Аутентифицирует пользователя через OAuth-провайдера.
        
        Args:
            user_info (dict[str, str]): Данные пользователя от OAuth.
            provider (str): Название провайдера.
            db (AsyncSession): Сессия базы данных.
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

        return await self._generate_tokens(user.email, response)

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

        email = await self._decode_jwt(refresh_token)
        return Token(access_token=await self._generate_jwt(email, days=1))

    async def _generate_tokens(self, email: str, response: Response) -> Token:
        """Создает access и refresh токены и устанавливает refresh token в cookies.
        
        Args:
            email (str): Email пользователя.
            response (Response): Объект ответа для установки cookies.

        Returns:
            Token: Сгенерированный access token.
        """
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
        """Генерирует JWT токен.
        
        Args:
            email (str): Email пользователя.
            minutes (int, optional): Количество минут до истечения токена. Defaults to 0.
            days (int, optional): Количество дней до истечения токена. Defaults to 0.

        Returns:
            str: Сгенерированный JWT токен.
        """
        expire = datetime.utcnow() + timedelta(minutes=minutes, days=days)
        return jwt.encode({"sub": email, "exp": expire}, settings.SECRET_KEY, algorithm="HS256")

    async def _decode_jwt(self, token: str) -> str:
        """Декодирует JWT токен и извлекает email.
        
        Args:
            token (str): JWT токен.

        Returns:
            str: Email пользователя.

        Raises:
            HTTPException: Если токен недействителен или истек.
        """
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



def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    repository = UserRepository(session)
    email_service = VerificationEmailService(session)
    return AuthService(repository, email_service)