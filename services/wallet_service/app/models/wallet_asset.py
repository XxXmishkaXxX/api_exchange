from sqlalchemy import Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.asset import Asset
from app.db.database import Base
import uuid




class WalletAssetBalance(Base):
    __tablename__ = "wallet_asset_balances"
    __table_args__ = (
        Index("idx_wallet_assets_wallet_asset", "wallet_id", "asset_id"),
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("wallets.id"), primary_key=True, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), primary_key=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    locked: Mapped[int] = mapped_column(Integer, default=0)

    wallet: Mapped["Wallet"] = relationship(back_populates="asset_balances")
    asset: Mapped["Asset"] = relationship(back_populates="wallet_asset_balances")
