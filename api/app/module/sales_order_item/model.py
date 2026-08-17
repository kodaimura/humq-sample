from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SalesOrderItem(Base):
    __tablename__ = "sales_order_item"
    __table_args__ = (UniqueConstraint("order_id", "product_id", name="uq_order_product"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales_order.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
