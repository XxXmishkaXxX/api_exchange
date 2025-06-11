from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.db.database import Base
from enum import Enum as PyEnum


class AssetStatus(str, PyEnum):
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    status =  Column(Enum(AssetStatus), nullable=False, default=AssetStatus.ACTIVATE)
    orders = relationship("Order", back_populates="order_asset", foreign_keys="[Order.order_asset_id]")
    payment_orders = relationship("Order", back_populates="payment_asset", foreign_keys="[Order.payment_asset_id]")

    def __repr__(self):
        return f"<Asset(id={self.id}, ticker='{self.ticker}', name='{self.name}')>"
