from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base



class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reset_code = Column(String(6), nullable=False)  # 6-значный код для сброса
    created_at = Column(DateTime, default=datetime.utcnow)  # Время генерации кода
    expires_at = Column(DateTime, nullable=False)  # Время истечения срока действия кода

    user = relationship("User", back_populates="reset_codes")
