from sqlalchemy import Column, Integer, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.schemas.order import StatusOrder, Direction, OrderType


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(StatusOrder), nullable=False, default="new")
    direction = Column(Enum(Direction), nullable=False)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)

    ticker = relationship("Ticker", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, type={self.type}, direction={self.direction}, ticker_id={self.ticker_id}, qty={self.qty}, price={self.price})>"