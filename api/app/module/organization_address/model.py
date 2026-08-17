from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import AddressKind


class OrganizationAddress(Base):
    __tablename__ = "organization_address"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AddressKind.SHIPPING.value
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    prefecture: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(200))
    recipient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
