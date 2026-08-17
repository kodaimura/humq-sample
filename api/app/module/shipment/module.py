from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.business_types import ShipmentStatus
from .model import Shipment


class ShipmentModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> Shipment:
        entity = Shipment(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, shipment_id: int) -> Shipment | None:
        return self.db.get(Shipment, shipment_id)

    def get_for_update(self, shipment_id: int) -> Shipment | None:
        stmt = select(Shipment).where(Shipment.id == shipment_id).with_for_update()
        return self.db.scalars(stmt).first()

    def list_by_order(self, order_id: int) -> list[Shipment]:
        stmt = select(Shipment).where(Shipment.order_id == order_id).order_by(Shipment.id)
        return list(self.db.scalars(stmt).all())

    def change_status(
        self, entity: Shipment, status: str, *, tracking_number: str | None = None
    ) -> str:
        previous = entity.status
        entity.status = status
        if tracking_number is not None:
            entity.tracking_number = tracking_number
        now = datetime.now(timezone.utc)
        if status == ShipmentStatus.CONFIRMED.value:
            entity.confirmed_at = now
        if status == ShipmentStatus.SHIPPED.value:
            entity.shipped_at = now
        self.db.flush()
        return previous
