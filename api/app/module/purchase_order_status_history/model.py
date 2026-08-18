from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PurchaseOrderStatusHistory(Base):
    __tablename__ = "purchase_order_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_order.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_by_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
