from fastapi import APIRouter, Depends, Response, Request
from app.services.auth import AuthService
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/register")
def register(data: RegisterRequest, service: AuthService = Depends(), db: Session = Depends(get_db)):
    return service.register_user(data, db)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, response: Response, service: AuthService = Depends(), db: Session = Depends(get_db)):
    return service.authenticate(data, db, response) 

@router.post("/token/refresh", response_model=Token)
def refresh(request: Request, service: AuthService = Depends(), db: Session = Depends(get_db)):
    return service.refresh_access_token(request)