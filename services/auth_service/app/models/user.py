from sqlalchemy import Column, String
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)  
    oauth_id = Column(String, nullable=True, unique=True) 