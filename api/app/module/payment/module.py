from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.module.business_types import PaymentStatus
from .model import Payment


class PaymentModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> Payment:
        entity = Payment(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> Payment | None:
        return self.db.get(Payment, entity_id)

    def get_for_update(self, entity_id: int) -> Payment | None:
        return self.db.scalars(
            select(Payment).where(Payment.id == entity_id).with_for_update()
        ).first()

    def list_by_payee(self, payee_organization_id: int) -> list[Payment]:
        return list(
            self.db.scalars(
                select(Payment)
                .where(Payment.payee_organization_id == payee_organization_id)
                .order_by(Payment.id.desc())
            ).all()
        )

    def post(self, entity: Payment) -> None:
        entity.status = PaymentStatus.POSTED.value
        entity.posted_at = datetime.now(timezone.utc)
        self.db.flush()

    def allocate(self, entity: Payment, amount: Decimal) -> bool:
        if amount <= 0 or amount > entity.unallocated_amount:
            return False
        entity.unallocated_amount -= amount
        self.db.flush()
        return True
