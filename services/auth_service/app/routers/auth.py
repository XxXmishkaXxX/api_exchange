from fastapi import APIRouter, Depends
from app.services.auth import AuthService
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


# 🔹 Регистрация (email + пароль)
@router.post("/register", response_model=Token)
def register(data: RegisterRequest, service: AuthService = Depends(), db: Session = Depends(get_db)):
    return service.register_user(data, db)

# 🔹 Логин (email + пароль)
@router.post("/login", response_model=Token)
def login(data: LoginRequest, service: AuthService = Depends(), db: Session = Depends(get_db)):
    return service.authenticate(data, db)