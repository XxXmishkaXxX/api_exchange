from typing import List
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Index, Enum as PG_ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.models.wallet_asset import WalletAssetBalance
from app.db.database import Base
import uuid
from enum import Enum


class WalletStatus(str, Enum):
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        Index("idx_wallet_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    status: Mapped[WalletStatus] = mapped_column(PG_ENUM(WalletStatus), nullable=False, default=WalletStatus.ACTIVATE)

    asset_balances: Mapped[List["WalletAssetBalance"]] = relationship(back_populates="wallet", cascade="all, delete-orphan")