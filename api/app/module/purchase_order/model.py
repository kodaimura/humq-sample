from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import PurchaseOrderStatus


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    buyer_organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organization.id"), index=True)
    supplier_organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organization.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouse.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default=PurchaseOrderStatus.DRAFT.value, index=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    note: Mapped[str | None] = mapped_column(Text)
    created_by_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
