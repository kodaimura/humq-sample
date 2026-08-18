from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import PaymentStatus


class Payment(Base):
    __tablename__ = "payment"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    payer_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    payee_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=PaymentStatus.DRAFT.value, index=True
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    unallocated_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    created_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id")
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
