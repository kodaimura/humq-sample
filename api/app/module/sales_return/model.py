from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import SalesReturnStatus


class SalesReturn(Base):
    __tablename__ = "sales_return"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    return_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sales_order.id"), index=True
    )
    customer_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouse.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=SalesReturnStatus.REQUESTED.value, index=True
    )
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    requested_credit_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0)
    requested_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
