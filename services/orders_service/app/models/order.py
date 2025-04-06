from sqlalchemy import Column, Integer, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.schemas.order import StatusOrder, Direction, OrderType
from app.models.asset import Asset


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(StatusOrder), nullable=False, default="new")
    direction = Column(Enum(Direction), nullable=False)
    
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    asset = relationship("Asset", back_populates="orders")

    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Order(id={self.id}, type={self.type}, direction={self.direction}, ticker={self.asset.ticker}, qty={self.qty}, price={self.price})>"
