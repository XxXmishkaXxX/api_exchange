from sqlalchemy.orm import Session
from app.models.user import User  
from app.schemas.auth import RegisterRequest
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

# Инициализация контекста для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User):

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"User with email {user.email} already exists.")
    
    def get_user_by_email(self, email: str):
        # Получаем пользователя по email
        return self.db.query(User).filter(User.email == email).first()

    def verify_password(self, provided_password: str, stored_password: str) -> bool:
        # Проверяем пароль
        return pwd_context.verify(provided_password, stored_password)

    def update_user(self, user_id: int, name: str = None, password: str = None):
        # Обновление пользователя
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if db_user:
            if name:
                db_user.name = name
            if password:
                db_user.password = pwd_context.hash(password)
            self.db.commit()
            self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: int):
        # Удаление пользователя
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
        return db_user
