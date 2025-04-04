from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.asset import Asset
from app.db.database import Base

class UserAssetBalance(Base):
    __tablename__ = "user_asset_balances"

    user_id = Column(Integer, nullable=False, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, primary_key=True)
    amount = Column(Integer, default=0)
    locked = Column(Integer, default=0)

    asset = relationship("Asset", back_populates="user_asset_balances")

    __table_args__ = (
        Index("idx_user_assets_user_asset", "user_id", "asset_id"),
    )