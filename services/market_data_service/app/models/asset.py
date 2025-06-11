from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.database import Base



class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    order_transactions: Mapped[list["Transaction"]] = relationship(
    	"Transaction",
    	back_populates="order_asset",
    	foreign_keys="[Transaction.order_asset_id]",
    	cascade="all, delete",
    	passive_deletes=True
	)
    payment_transactions: Mapped[list["Transaction"]] = relationship(
    	"Transaction",
    	back_populates="payment_asset",
    	foreign_keys="[Transaction.payment_asset_id]",
    	cascade="all, delete",
    	passive_deletes=True
	)

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, ticker={self.ticker}, name={self.name})>"
