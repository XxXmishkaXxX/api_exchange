from sqlalchemy import Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.asset import Asset
from app.db.database import Base
import uuid

class UserAssetBalance(Base):
    __tablename__ = "user_asset_balances"
    __table_args__ = (
        Index("idx_user_assets_user_asset", "user_id", "asset_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), primary_key=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    locked: Mapped[int] = mapped_column(Integer, default=0)

    asset: Mapped["Asset"] = relationship(back_populates="user_asset_balances")
