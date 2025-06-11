from sqlalchemy import Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.schemas.order import StatusOrder, Direction
from app.models.asset import Asset

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[PG_UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[PG_UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    status: Mapped[StatusOrder] = mapped_column(Enum(StatusOrder), nullable=False, default=StatusOrder.NEW)
    direction: Mapped[Direction] = mapped_column(Enum(Direction), nullable=False)

    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    order_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    order_asset: Mapped["Asset"] = relationship("Asset", back_populates="orders", foreign_keys=[order_asset_id])

    payment_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    payment_asset: Mapped["Asset"] = relationship("Asset", back_populates="payment_orders", foreign_keys=[payment_asset_id])

    filled: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return (
            f"<Order("
            f"id={self.id}, "
            f"type={self.type}, "
            f"direction={self.direction}, "
            f"ticker={self.order_asset.ticker}, "
            f"qty={self.qty}, "
            f"price={self.price}, "
            f"payment_asset={self.payment_asset.ticker}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at},"
            f"filled={self.filled}"
            f")>"
        )

