from fastapi import APIRouter, Depends, Response, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from app.services.auth import AuthService
from app.db.database import get_db
from app.core.config import settings

router = APIRouter()

# OAuth конфигурация
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.OAUTH2_CLIENT_ID,
    client_secret=settings.OAUTH2_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url= 'https://accounts.google.com/.well-known/openid-configuration'
)

# oauth.register(
#     name="vk",
#     client_id="YOUR_VK_CLIENT_ID",
#     client_secret="YOUR_VK_CLIENT_SECRET",
#     authorize_url="https://oauth.vk.com/authorize",
#     access_token_url="https://oauth.vk.com/access_token",
#     client_kwargs={"scope": "email"},
# )

# === Google OAuth ===
@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_google(request: Request, response: Response, service: AuthService = Depends(), db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token['userinfo']

    if not user_info:
        raise HTTPException(status_code=400, detail="Ошибка авторизации Google")
    
    user = await service.oauth_authenticate(user_info=user_info, provider="google", db=db, response=response)

    return user


# # === VK OAuth ===
# @router.get("/login/vk")
# async def login_vk(request: Request):
#     redirect_uri = request.url_for("auth_vk")
#     return await oauth.vk.authorize_redirect(request, redirect_uri)


# @router.get("/vk/callback")
# async def auth_vk(request: Request, service: AuthService = Depends(), db: Session = Depends(get_db)):
#     token = await oauth.vk.authorize_access_token(request)
    
#     user_info_url = f"https://api.vk.com/method/users.get?access_token={token['access_token']}&v=5.131&fields=email"
    
#     async with httpx.AsyncClient() as client:
#         response = await client.get(user_info_url)

#     user_info = response.json()
    
#     if "response" not in user_info or not user_info["response"]:
#         raise HTTPException(status_code=400, detail="Ошибка авторизации VK")

#     vk_user = user_info["response"][0]
#     email = token.get("email", "")  # У VK email приходит отдельно

#     return service.oauth_authenticate({"id": vk_user["id"], "email": email, "name": vk_user["first_name"]}, db)
