from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryAdjustmentItem(Base):
    __tablename__ = "inventory_adjustment_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    adjustment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("inventory_adjustment.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True
    )
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
