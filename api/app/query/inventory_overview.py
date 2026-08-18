from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.module.inventory_balance.model import InventoryBalance
from app.module.product.model import Product
from app.module.warehouse.model import Warehouse


@dataclass(frozen=True)
class InventoryOverview:
    balance_id: int
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    product_id: int
    sku: str
    product_name: str
    on_hand_quantity: int
    reserved_quantity: int
    available_quantity: int


class InventoryOverviewQuery:
    def __init__(self, db: Session):
        self.db = db

    def list_by_organization(self, organization_id: int) -> list[InventoryOverview]:
        stmt = (
            select(
                InventoryBalance.id.label("balance_id"),
                Warehouse.id.label("warehouse_id"),
                Warehouse.code.label("warehouse_code"),
                Warehouse.name.label("warehouse_name"),
                Product.id.label("product_id"),
                Product.sku,
                Product.name.label("product_name"),
                InventoryBalance.on_hand_quantity,
                InventoryBalance.reserved_quantity,
                (
                    InventoryBalance.on_hand_quantity
                    - InventoryBalance.reserved_quantity
                ).label("available_quantity"),
            )
            .join(Warehouse, Warehouse.id == InventoryBalance.warehouse_id)
            .join(Product, Product.id == InventoryBalance.product_id)
            .where(Warehouse.organization_id == organization_id)
            .order_by(Warehouse.code, Product.sku)
        )
        return [InventoryOverview(**row._mapping) for row in self.db.execute(stmt)]
