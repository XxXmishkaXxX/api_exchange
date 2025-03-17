from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


from app.db.database import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    orders = relationship("Order", back_populates="ticker", cascade="all, delete")

    def __repr__(self):
        return f"<Ticker(id={self.id}, symbol={self.symbol}, name={self.name})>"

