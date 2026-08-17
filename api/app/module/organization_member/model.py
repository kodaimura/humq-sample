from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import MemberRole


class OrganizationMember(Base):
    __tablename__ = "organization_member"
    __table_args__ = (
        UniqueConstraint("organization_id", "account_id", name="uq_organization_member"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MemberRole.CUSTOMER.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
