from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import GoodsReceiptStatus


class GoodsReceipt(Base):
    __tablename__ = "goods_receipt"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_order.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouse.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=GoodsReceiptStatus.DRAFT.value, index=True)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(Text)
    received_by_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
