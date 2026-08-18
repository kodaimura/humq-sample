from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import PaymentAllocation


class PaymentAllocationModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> PaymentAllocation:
        entity = PaymentAllocation(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_payment(self, payment_id: int) -> list[PaymentAllocation]:
        return list(
            self.db.scalars(
                select(PaymentAllocation)
                .where(PaymentAllocation.payment_id == payment_id)
                .order_by(PaymentAllocation.id)
            ).all()
        )

    def list_by_invoice(self, invoice_id: int) -> list[PaymentAllocation]:
        return list(
            self.db.scalars(
                select(PaymentAllocation)
                .where(PaymentAllocation.invoice_id == invoice_id)
                .order_by(PaymentAllocation.id)
            ).all()
        )
