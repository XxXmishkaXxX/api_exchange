from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.database import Base



class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    reset_code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)  
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="reset_codes")
