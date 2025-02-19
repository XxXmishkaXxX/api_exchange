from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base



class EmailVerification(Base):
    __tablename__ = 'email_verifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    verification_code = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="email_verifications")