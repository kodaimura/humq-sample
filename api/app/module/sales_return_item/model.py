from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SalesReturnItem(Base):
    __tablename__ = "sales_return_item"
    __table_args__ = (
        UniqueConstraint("sales_return_id", "order_item_id", name="uq_sales_return_order_item"),
        CheckConstraint("requested_quantity > 0", name="ck_sales_return_item_quantity"),
        CheckConstraint("received_quantity >= 0 AND received_quantity <= requested_quantity", name="ck_sales_return_item_received"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sales_return_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sales_return.id"), index=True)
    order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sales_order_item.id"), index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product.id"), index=True)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    restocked_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discarded_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def remaining_quantity(self) -> int:
        return self.requested_quantity - self.received_quantity
