from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


from app.db.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    order_transactions = relationship(
        "Transaction",
        back_populates="order_asset",
        foreign_keys="Transaction.order_asset_id"
    )
    payment_transactions = relationship(
        "Transaction",
        back_populates="payment_asset",
        foreign_keys="Transaction.payment_asset_id"
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, ticker={self.ticker}, name={self.name})>"

