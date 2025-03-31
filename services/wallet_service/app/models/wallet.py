from sqlalchemy import Column, Integer, String, Float, Index
from app.db.database import Base


class UserAssetBalance(Base):
    __tablename__ = "user_asset_balances"

    user_id = Column(Integer, nullable=False, primary_key=True)
    ticker_id = Column(String, nullable=False, primary_key=True)
    amount = Column(Float, default=0.0)
    locked = Column(Float, default=0.0)

    __table_args__ = (
        Index("idx_user_assets_user_ticker", "user_id", "ticker_id")
    )