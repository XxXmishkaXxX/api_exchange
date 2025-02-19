from sqlalchemy import Column, String, Integer, Boolean
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)  
    oauth_id = Column(String, nullable=True, unique=True)
    is_verified = Column(Boolean, default=False)
