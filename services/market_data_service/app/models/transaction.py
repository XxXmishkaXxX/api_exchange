from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    order_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    order_asset = relationship("Asset", back_populates="order_transactions", foreign_keys=[order_asset_id])

    payment_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    payment_asset = relationship("Asset", back_populates="payment_transactions", foreign_keys=[payment_asset_id])

    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=func.now())

    price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_transaction_pair", "order_asset_id", "payment_asset_id"),
    )