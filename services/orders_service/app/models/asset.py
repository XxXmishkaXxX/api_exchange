from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    orders = relationship("Order", back_populates="asset")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, ticker={self.ticker}, name={self.name})>"

