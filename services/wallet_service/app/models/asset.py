from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from typing import List

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    wallet_asset_balances : Mapped[List["WalletAssetBalance"]] = relationship(
        back_populates="asset"
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, ticker={self.ticker}, name={self.name})>"
