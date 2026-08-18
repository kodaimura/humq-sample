from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_item"
    __table_args__ = (
        UniqueConstraint("goods_receipt_id", "purchase_order_item_id", name="uq_goods_receipt_order_item"),
        CheckConstraint("quantity > 0", name="ck_goods_receipt_quantity"),
        CheckConstraint("accepted_quantity + rejected_quantity = quantity", name="ck_goods_receipt_disposition"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    goods_receipt_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("goods_receipt.id"), index=True)
    purchase_order_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_order_item.id"), index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
