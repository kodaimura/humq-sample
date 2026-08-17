from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import OrderStatus


class SalesOrder(Base):
    __tablename__ = "sales_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    seller_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    customer_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    shipping_address_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("organization_address.id")
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=OrderStatus.DRAFT.value, index=True
    )
    requested_ship_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(Text)
    ordered_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
