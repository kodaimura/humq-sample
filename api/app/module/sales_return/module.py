from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.module.business_types import SalesReturnStatus
from .model import SalesReturn


class SalesReturnModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> SalesReturn:
        entity = SalesReturn(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> SalesReturn | None:
        return self.db.get(SalesReturn, entity_id)

    def get_for_update(self, entity_id: int) -> SalesReturn | None:
        return self.db.scalars(
            select(SalesReturn).where(SalesReturn.id == entity_id).with_for_update()
        ).first()

    def list_by_order(self, order_id: int) -> list[SalesReturn]:
        return list(
            self.db.scalars(
                select(SalesReturn)
                .where(SalesReturn.order_id == order_id)
                .order_by(SalesReturn.id.desc())
            ).all()
        )

    def list_by_customer(self, customer_organization_id: int) -> list[SalesReturn]:
        return list(
            self.db.scalars(
                select(SalesReturn)
                .where(SalesReturn.customer_organization_id == customer_organization_id)
                .order_by(SalesReturn.id.desc())
            ).all()
        )

    def set_requested_credit_amount(
        self, entity: SalesReturn, amount: Decimal
    ) -> SalesReturn:
        entity.requested_credit_amount = amount
        self.db.flush()
        return entity

    def change_status(self, entity: SalesReturn, status: str) -> str:
        previous = entity.status
        entity.status = status
        entity.version += 1
        now = datetime.now(timezone.utc)
        if status == SalesReturnStatus.APPROVED.value:
            entity.approved_at = now
        if status == SalesReturnStatus.COMPLETED.value:
            entity.completed_at = now
        if status == SalesReturnStatus.CANCELED.value:
            entity.canceled_at = now
        self.db.flush()
        return previous
