from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.schemas.order import StatusOrder, Direction, OrderType
from app.models.asset import Asset


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)

    type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(StatusOrder), nullable=False, default=StatusOrder.NEW)
    direction = Column(Enum(Direction), nullable=False)

    qty = Column(Integer, nullable=False)
    price = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    order_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    order_asset = relationship("Asset", back_populates="orders", foreign_keys=[order_asset_id])

    payment_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    payment_asset = relationship("Asset", back_populates="payment_orders", foreign_keys=[payment_asset_id])

    def __repr__(self):
        return (
            f"<Order("
            f"id={self.id}, "
            f"type={self.type}, "
            f"direction={self.direction}, "
            f"ticker={self.order_asset.ticker}, "
            f"qty={self.qty}, "
            f"price={self.price}, "
            f"payment_asset={self.payment_asset.ticker}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at}"
            f")>"
        )
