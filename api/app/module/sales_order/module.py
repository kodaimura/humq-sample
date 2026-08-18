from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.business_types import OrderStatus
from .model import SalesOrder


class SalesOrderModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> SalesOrder:
        entity = SalesOrder(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, order_id: int) -> SalesOrder | None:
        return self.db.get(SalesOrder, order_id)

    def get_for_update(self, order_id: int) -> SalesOrder | None:
        stmt = select(SalesOrder).where(SalesOrder.id == order_id).with_for_update()
        return self.db.scalars(stmt).first()

    def list_by_seller(self, seller_organization_id: int) -> list[SalesOrder]:
        stmt = (
            select(SalesOrder)
            .where(SalesOrder.seller_organization_id == seller_organization_id)
            .order_by(SalesOrder.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def set_totals(
        self,
        entity: SalesOrder,
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

    def change_status(self, entity: SalesOrder, status: str) -> str:
        previous = entity.status
        entity.status = status
        entity.version += 1
        now = datetime.now(timezone.utc)
        if (
            status
            in {
                OrderStatus.CONFIRMED.value,
                OrderStatus.PARTIALLY_ALLOCATED.value,
                OrderStatus.ALLOCATED.value,
            }
            and entity.confirmed_at is None
        ):
            entity.confirmed_at = now
        if status == OrderStatus.CANCELED.value:
            entity.canceled_at = now
        self.db.flush()
        return previous
