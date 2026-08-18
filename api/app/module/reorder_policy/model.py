from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReorderPolicy(Base):
    __tablename__ = "reorder_policy"
    __table_args__ = (UniqueConstraint("warehouse_id", "product_id", name="uq_reorder_policy"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouse.id"), index=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product.id"), index=True)
    preferred_supplier_organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organization.id"))
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False)
    target_stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
