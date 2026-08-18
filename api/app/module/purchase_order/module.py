from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.business_types import PurchaseOrderStatus
from .model import PurchaseOrder


class PurchaseOrderModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> PurchaseOrder:
        entity = PurchaseOrder(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def get_by_id(self, entity_id: int) -> PurchaseOrder | None: return self.db.get(PurchaseOrder, entity_id)
    def get_for_update(self, entity_id: int) -> PurchaseOrder | None:
        return self.db.scalars(select(PurchaseOrder).where(PurchaseOrder.id == entity_id).with_for_update()).first()
    def list_by_buyer(self, buyer_organization_id: int) -> list[PurchaseOrder]:
        return list(self.db.scalars(select(PurchaseOrder).where(PurchaseOrder.buyer_organization_id == buyer_organization_id).order_by(PurchaseOrder.id.desc())).all())
    def set_totals(self, entity: PurchaseOrder, *, subtotal: Decimal, tax_amount: Decimal, total_amount: Decimal) -> None:
        entity.subtotal = subtotal; entity.tax_amount = tax_amount; entity.total_amount = total_amount; entity.version += 1; self.db.flush()
    def change_status(self, entity: PurchaseOrder, status: str) -> str:
        previous = entity.status; entity.status = status; entity.version += 1; now = datetime.now(timezone.utc)
        if status == PurchaseOrderStatus.APPROVED.value: entity.approved_at = now
        if status == PurchaseOrderStatus.CANCELED.value: entity.canceled_at = now
        self.db.flush(); return previous
