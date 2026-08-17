from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.module.business_types import OutboxStatus


class OutboxEvent(Base):
    __tablename__ = "outbox_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OutboxStatus.PENDING.value, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
