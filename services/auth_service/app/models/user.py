from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db.database import Base
from sqlalchemy.orm import relationship
from app.models.email import EmailVerification
from app.models.password_reset import PasswordResetCode


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=True)
    role = Column(String, default="USER")
    oauth_provider = Column(String, nullable=True)  
    oauth_id = Column(String, nullable=True, unique=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    email_verifications = relationship("EmailVerification", back_populates="user")
    reset_codes = relationship("PasswordResetCode", back_populates="user")