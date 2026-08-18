from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoice"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    seller_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    customer_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales_order.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=InvoiceStatus.DRAFT.value, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    created_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id")
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def balance_due(self) -> Decimal:
        return self.total_amount - self.paid_amount
