from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.module.business_types import InvoiceStatus
from .model import Invoice


class InvoiceModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> Invoice:
        entity = Invoice(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> Invoice | None:
        return self.db.get(Invoice, entity_id)

    def get_for_update(self, entity_id: int) -> Invoice | None:
        return self.db.scalars(
            select(Invoice).where(Invoice.id == entity_id).with_for_update()
        ).first()

    def list_by_seller(self, seller_organization_id: int) -> list[Invoice]:
        return list(
            self.db.scalars(
                select(Invoice)
                .where(Invoice.seller_organization_id == seller_organization_id)
                .order_by(Invoice.id.desc())
            ).all()
        )

    def list_by_order(self, order_id: int) -> list[Invoice]:
        return list(
            self.db.scalars(
                select(Invoice)
                .where(Invoice.order_id == order_id)
                .order_by(Invoice.id.desc())
            ).all()
        )

    def set_totals(
        self,
        entity: Invoice,
        *,
        subtotal: Decimal,
        tax_amount: Decimal,
        total_amount: Decimal,
    ) -> None:
        entity.subtotal = subtotal
        entity.tax_amount = tax_amount
        entity.total_amount = total_amount
        entity.version += 1
        self.db.flush()

    def change_status(self, entity: Invoice, status: str) -> str:
        previous = entity.status
        entity.status = status
        entity.version += 1
        now = datetime.now(timezone.utc)
        if status == InvoiceStatus.ISSUED.value:
            entity.issued_at = now
        if status == InvoiceStatus.VOID.value:
            entity.voided_at = now
        self.db.flush()
        return previous

    def apply_payment(self, entity: Invoice, amount: Decimal) -> str:
        if amount <= 0 or amount > entity.balance_due:
            raise ValueError("payment exceeds invoice balance")
        previous = entity.status
        entity.paid_amount += amount
        entity.version += 1
        entity.status = (
            InvoiceStatus.PAID.value
            if entity.balance_due == 0
            else InvoiceStatus.PARTIALLY_PAID.value
        )
        self.db.flush()
        return previous
