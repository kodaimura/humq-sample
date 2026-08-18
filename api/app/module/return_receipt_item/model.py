from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReturnReceiptItem(Base):
    __tablename__ = "return_receipt_item"
    __table_args__ = (
        UniqueConstraint("return_receipt_id", "sales_return_item_id", name="uq_return_receipt_item"),
        CheckConstraint("quantity > 0", name="ck_return_receipt_item_quantity"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    return_receipt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("return_receipt.id"), index=True)
    sales_return_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sales_return_item.id"), index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    disposition: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
