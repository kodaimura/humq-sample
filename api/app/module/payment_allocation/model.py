from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PaymentAllocation(Base):
    __tablename__ = "payment_allocation"
    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_id", name="uq_payment_invoice"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("payment.id"), index=True
    )
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("invoice.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    allocated_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
