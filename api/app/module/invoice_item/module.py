from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .model import InvoiceItem


class InvoiceItemModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> InvoiceItem:
        entity = InvoiceItem(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def list_by_invoice(self, invoice_id: int) -> list[InvoiceItem]:
        return list(self.db.scalars(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id).order_by(InvoiceItem.id)).all())
    def invoiced_quantity_for_shipment_item(self, shipment_item_id: int) -> int:
        return int(self.db.scalar(select(func.coalesce(func.sum(InvoiceItem.quantity), 0)).where(InvoiceItem.shipment_item_id == shipment_item_id)) or 0)
