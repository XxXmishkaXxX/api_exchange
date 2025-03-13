from sqlalchemy import Column, Integer, String, Float, Enum
from enum import Enum as PyEnum
from app.db.database import Base

class Direction(str, PyEnum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, PyEnum):
    MARKET = "market"
    LIMIT = "limit"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    direction = Column(Enum(Direction), nullable=False)
    ticker = Column(String(10), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Order(id={self.id}, type={self.type}, direction={self.direction}, ticker={self.ticker}, qty={self.qty}, price={self.price})>"