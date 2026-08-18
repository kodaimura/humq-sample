from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_item"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "product_id", name="uq_purchase_order_product"),
        CheckConstraint("quantity > 0", name="ck_purchase_order_item_quantity"),
        CheckConstraint("received_quantity >= 0 AND received_quantity <= quantity", name="ck_purchase_order_item_received"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_order.id"), index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product.id"), index=True)
    supplier_product_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("supplier_product.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.received_quantity
