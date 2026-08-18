from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Warehouse


class WarehouseModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, organization_id: int, code: str, name: str) -> Warehouse:
        entity = Warehouse(organization_id=organization_id, code=code, name=name)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, warehouse_id: int) -> Warehouse | None:
        return self.db.get(Warehouse, warehouse_id)

    def list_by_organization(self, organization_id: int) -> list[Warehouse]:
        stmt = (
            select(Warehouse)
            .where(Warehouse.organization_id == organization_id)
            .order_by(Warehouse.code)
        )
        return list(self.db.scalars(stmt).all())
