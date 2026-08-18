from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import InvoiceStatusHistory


class InvoiceStatusHistoryModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> InvoiceStatusHistory:
        entity = InvoiceStatusHistory(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def list_by_invoice(self, invoice_id: int) -> list[InvoiceStatusHistory]:
        return list(
            self.db.scalars(
                select(InvoiceStatusHistory)
                .where(InvoiceStatusHistory.invoice_id == invoice_id)
                .order_by(InvoiceStatusHistory.id)
            ).all()
        )
