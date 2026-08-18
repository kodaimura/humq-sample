from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import ReservationStatus


class StockReservation(Base):
    __tablename__ = "stock_reservation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales_order_item.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouse.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReservationStatus.ACTIVE.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
