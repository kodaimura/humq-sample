from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.module.inventory_balance.model import InventoryBalance
from app.module.organization.model import Organization
from app.module.product.model import Product
from app.module.purchase_order.model import PurchaseOrder
from app.module.purchase_order_item.model import PurchaseOrderItem
from app.module.reorder_policy.model import ReorderPolicy
from app.module.warehouse.model import Warehouse


@dataclass(frozen=True)
class ReorderPolicySnapshot:
    policy_id: int
    warehouse_id: int
    warehouse_name: str
    product_id: int
    sku: str
    product_name: str
    supplier_organization_id: int | None
    supplier_name: str | None
    available_quantity: int
    reorder_point: int
    target_stock_quantity: int


@dataclass(frozen=True)
class PurchaseOrderOverview:
    id: int
    purchase_order_number: str
    supplier_name: str
    warehouse_name: str
    status: str
    line_count: int
    ordered_quantity: int
    received_quantity: int
    total_amount: Decimal


class ProcurementOverviewQuery:
    def __init__(self, db: Session):
        self.db = db

    def reorder_policy_snapshots(
        self, organization_id: int
    ) -> list[ReorderPolicySnapshot]:
        supplier = Organization.__table__.alias("supplier")
        stmt = (
            select(
                ReorderPolicy.id,
                Warehouse.id,
                Warehouse.name,
                Product.id,
                Product.sku,
                Product.name,
                ReorderPolicy.preferred_supplier_organization_id,
                supplier.c.name,
                func.coalesce(
                    InventoryBalance.on_hand_quantity
                    - InventoryBalance.reserved_quantity,
                    0,
                ),
                ReorderPolicy.reorder_point,
                ReorderPolicy.target_stock_quantity,
            )
            .join(Warehouse, Warehouse.id == ReorderPolicy.warehouse_id)
            .join(Product, Product.id == ReorderPolicy.product_id)
            .outerjoin(
                InventoryBalance,
                (InventoryBalance.warehouse_id == ReorderPolicy.warehouse_id)
                & (InventoryBalance.product_id == ReorderPolicy.product_id),
            )
            .outerjoin(
                supplier,
                supplier.c.id == ReorderPolicy.preferred_supplier_organization_id,
            )
            .where(
                Warehouse.organization_id == organization_id,
                ReorderPolicy.active.is_(True),
            )
            .order_by(Warehouse.code, Product.sku)
        )
        return [ReorderPolicySnapshot(*row) for row in self.db.execute(stmt)]

    def purchase_orders(self, organization_id: int) -> list[PurchaseOrderOverview]:
        stmt = (
            select(
                PurchaseOrder.id,
                PurchaseOrder.purchase_order_number,
                Organization.name,
                Warehouse.name,
                PurchaseOrder.status,
                func.count(PurchaseOrderItem.id),
                func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
                func.coalesce(func.sum(PurchaseOrderItem.received_quantity), 0),
                PurchaseOrder.total_amount,
            )
            .join(
                Organization, Organization.id == PurchaseOrder.supplier_organization_id
            )
            .join(Warehouse, Warehouse.id == PurchaseOrder.warehouse_id)
            .outerjoin(
                PurchaseOrderItem,
                PurchaseOrderItem.purchase_order_id == PurchaseOrder.id,
            )
            .where(PurchaseOrder.buyer_organization_id == organization_id)
            .group_by(PurchaseOrder.id, Organization.name, Warehouse.name)
            .order_by(PurchaseOrder.id.desc())
        )
        return [PurchaseOrderOverview(*row) for row in self.db.execute(stmt)]
