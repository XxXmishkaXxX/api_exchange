from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    orders = relationship("Order", back_populates="order_asset", foreign_keys="[Order.order_asset_id]")
    payment_orders = relationship("Order", back_populates="payment_asset", foreign_keys="[Order.payment_asset_id]")

    def __repr__(self):
        return f"<Asset(id={self.id}, ticker='{self.ticker}', name='{self.name}')>"
