from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.module.organization.model import Organization
from app.module.sales_order.model import SalesOrder
from app.module.shipment.model import Shipment
from app.module.shipment_item.model import ShipmentItem
from app.module.warehouse.model import Warehouse


@dataclass(frozen=True)
class ShipmentOverview:
    id: int
    shipment_number: str
    order_id: int
    order_number: str
    customer_name: str
    warehouse_name: str
    status: str
    item_count: int
    total_quantity: int
    tracking_number: str | None
    shipped_at: datetime | None
    created_at: datetime


class ShipmentOverviewQuery:
    def __init__(self, db: Session):
        self.db = db

    def list_by_seller(self, seller_organization_id: int) -> list[ShipmentOverview]:
        stmt = (
            select(
                Shipment.id,
                Shipment.shipment_number,
                SalesOrder.id.label("order_id"),
                SalesOrder.order_number,
                Organization.name.label("customer_name"),
                Warehouse.name.label("warehouse_name"),
                Shipment.status,
                func.count(ShipmentItem.id).label("item_count"),
                func.coalesce(func.sum(ShipmentItem.quantity), 0).label(
                    "total_quantity"
                ),
                Shipment.tracking_number,
                Shipment.shipped_at,
                Shipment.created_at,
            )
            .join(SalesOrder, SalesOrder.id == Shipment.order_id)
            .join(Organization, Organization.id == SalesOrder.customer_organization_id)
            .join(Warehouse, Warehouse.id == Shipment.warehouse_id)
            .outerjoin(ShipmentItem, ShipmentItem.shipment_id == Shipment.id)
            .where(SalesOrder.seller_organization_id == seller_organization_id)
            .group_by(Shipment.id, SalesOrder.id, Organization.id, Warehouse.id)
            .order_by(Shipment.id.desc())
        )
        return [ShipmentOverview(**row._mapping) for row in self.db.execute(stmt)]
