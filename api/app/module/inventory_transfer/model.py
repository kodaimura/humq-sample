from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import TransferStatus


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfer"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouse.id"), nullable=False, index=True
    )
    destination_warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouse.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TransferStatus.DRAFT.value
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_by_account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("account.id"), nullable=False
    )
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
