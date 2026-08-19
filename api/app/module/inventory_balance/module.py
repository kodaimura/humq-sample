from typing import Literal, overload

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import InventoryBalance


class InventoryBalanceModule:
    def __init__(self, db: Session):
        self.db = db

    def get(self, *, warehouse_id: int, product_id: int) -> InventoryBalance | None:
        stmt = select(InventoryBalance).where(
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.product_id == product_id,
        )
        return self.db.scalars(stmt).first()

    @overload
    def get_for_update(
        self, *, warehouse_id: int, product_id: int, create: Literal[True]
    ) -> InventoryBalance: ...

    @overload
    def get_for_update(
        self, *, warehouse_id: int, product_id: int, create: bool = False
    ) -> InventoryBalance | None: ...

    def get_for_update(
        self, *, warehouse_id: int, product_id: int, create: bool = False
    ) -> InventoryBalance | None:
        stmt = (
            select(InventoryBalance)
            .where(
                InventoryBalance.warehouse_id == warehouse_id,
                InventoryBalance.product_id == product_id,
            )
            .with_for_update()
        )
        entity = self.db.scalars(stmt).first()
        if entity is None and create:
            entity = InventoryBalance(warehouse_id=warehouse_id, product_id=product_id)
            self.db.add(entity)
            self.db.flush()
            self.db.refresh(entity)
        return entity

    def list_by_warehouse(self, warehouse_id: int) -> list[InventoryBalance]:
        stmt = (
            select(InventoryBalance)
            .where(InventoryBalance.warehouse_id == warehouse_id)
            .order_by(InventoryBalance.product_id)
        )
        return list(self.db.scalars(stmt).all())

    def adjust_on_hand(self, entity: InventoryBalance, quantity_delta: int) -> bool:
        next_quantity = entity.on_hand_quantity + quantity_delta
        if next_quantity < entity.reserved_quantity or next_quantity < 0:
            return False
        entity.on_hand_quantity = next_quantity
        entity.version += 1
        self.db.flush()
        return True

    def reserve(self, entity: InventoryBalance, quantity: int) -> bool:
        if quantity <= 0 or entity.available_quantity < quantity:
            return False
        entity.reserved_quantity += quantity
        entity.version += 1
        self.db.flush()
        return True

    def release(self, entity: InventoryBalance, quantity: int) -> bool:
        if quantity <= 0 or entity.reserved_quantity < quantity:
            return False
        entity.reserved_quantity -= quantity
        entity.version += 1
        self.db.flush()
        return True

    def consume_reserved(self, entity: InventoryBalance, quantity: int) -> bool:
        if (
            quantity <= 0
            or entity.reserved_quantity < quantity
            or entity.on_hand_quantity < quantity
        ):
            return False
        entity.reserved_quantity -= quantity
        entity.on_hand_quantity -= quantity
        entity.version += 1
        self.db.flush()
        return True
