from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .model import SalesReturnItem


class SalesReturnItemModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> SalesReturnItem:
        entity = SalesReturnItem(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> SalesReturnItem | None:
        return self.db.get(SalesReturnItem, entity_id)

    def get_for_update(self, entity_id: int) -> SalesReturnItem | None:
        return self.db.scalars(
            select(SalesReturnItem)
            .where(SalesReturnItem.id == entity_id)
            .with_for_update()
        ).first()

    def list_by_return(self, sales_return_id: int) -> list[SalesReturnItem]:
        return list(
            self.db.scalars(
                select(SalesReturnItem)
                .where(SalesReturnItem.sales_return_id == sales_return_id)
                .order_by(SalesReturnItem.id)
            ).all()
        )

    def total_requested_for_order_item(self, order_item_id: int) -> int:
        return int(
            self.db.scalar(
                select(
                    func.coalesce(func.sum(SalesReturnItem.requested_quantity), 0)
                ).where(SalesReturnItem.order_item_id == order_item_id)
            )
            or 0
        )

    def receive(
        self, entity: SalesReturnItem, *, quantity: int, restocked: int, discarded: int
    ) -> bool:
        if (
            quantity <= 0
            or restocked + discarded != quantity
            or entity.received_quantity + quantity > entity.requested_quantity
        ):
            return False
        entity.received_quantity += quantity
        entity.restocked_quantity += restocked
        entity.discarded_quantity += discarded
        self.db.flush()
        return True
