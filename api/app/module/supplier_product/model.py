from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SupplierProduct(Base):
    __tablename__ = "supplier_product"
    __table_args__ = (
        UniqueConstraint(
            "supplier_organization_id", "product_id", name="uq_supplier_product"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("product.id"), index=True
    )
    supplier_sku: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minimum_order_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
