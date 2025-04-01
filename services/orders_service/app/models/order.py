from sqlalchemy import Column, Integer, Enum, Float
from app.db.database import Base
from app.schemas.order import StatusOrder, Direction, OrderType


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(StatusOrder), nullable=False, default="new")
    direction = Column(Enum(Direction), nullable=False)
    ticker_id = Column(Integer, nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)


    def __repr__(self):
        return f"<Order(id={self.id}, type={self.type}, direction={self.direction}, ticker_id={self.ticker_id}, qty={self.qty}, price={self.price})>"