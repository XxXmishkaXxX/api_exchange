from sqlalchemy import DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    order_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    order_asset: Mapped["Asset"] = relationship(
        "Asset",
        back_populates="order_transactions",
        foreign_keys=[order_asset_id]
    )

    payment_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    payment_asset: Mapped["Asset"] = relationship(
        "Asset",
        back_populates="payment_transactions",
        foreign_keys=[payment_asset_id]
    )

    from_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    to_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    price: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_transaction_pair", "order_asset_id", "payment_asset_id"),
    )
