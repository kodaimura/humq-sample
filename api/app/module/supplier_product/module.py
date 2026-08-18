from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import SupplierProduct


class SupplierProductModule:
    def __init__(self, db: Session): self.db = db
    def create(self, **values) -> SupplierProduct:
        entity = SupplierProduct(**values); self.db.add(entity); self.db.flush(); self.db.refresh(entity); return entity
    def get_by_id(self, entity_id: int) -> SupplierProduct | None: return self.db.get(SupplierProduct, entity_id)
    def get(self, *, supplier_organization_id: int, product_id: int) -> SupplierProduct | None:
        return self.db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_organization_id == supplier_organization_id, SupplierProduct.product_id == product_id)).first()
    def list_by_supplier(self, supplier_organization_id: int) -> list[SupplierProduct]:
        return list(self.db.scalars(select(SupplierProduct).where(SupplierProduct.supplier_organization_id == supplier_organization_id).order_by(SupplierProduct.id)).all())
