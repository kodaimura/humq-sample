from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ShipmentItem(Base):
    __tablename__ = "shipment_item"
    __table_args__ = (
        UniqueConstraint("shipment_id", "order_item_id", name="uq_shipment_order_item"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("shipment.id"), nullable=False, index=True
    )
    order_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales_order_item.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
