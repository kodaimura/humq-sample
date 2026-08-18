from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.module.business_types import OrderStatus
from app.module.inventory_balance.model import InventoryBalance
from app.module.sales_order.model import SalesOrder
from app.module.warehouse.model import Warehouse


@dataclass(frozen=True)
class OperationsDashboard:
    open_order_count: int
    ready_to_ship_count: int
    shipped_order_count: int
    total_order_amount: Decimal
    low_stock_count: int


class OperationsDashboardQuery:
    def __init__(self, db: Session):
        self.db = db

    def get(self, organization_id: int) -> OperationsDashboard:
        order_stmt = select(
            func.count(
                case(
                    (
                        SalesOrder.status.not_in(
                            [OrderStatus.SHIPPED.value, OrderStatus.CANCELED.value]
                        ),
                        1,
                    )
                )
            ).label("open_order_count"),
            func.count(
                case((SalesOrder.status == OrderStatus.ALLOCATED.value, 1))
            ).label("ready_to_ship_count"),
            func.count(case((SalesOrder.status == OrderStatus.SHIPPED.value, 1))).label(
                "shipped_order_count"
            ),
            func.coalesce(func.sum(SalesOrder.total_amount), 0).label(
                "total_order_amount"
            ),
        ).where(SalesOrder.seller_organization_id == organization_id)
        order_row = self.db.execute(order_stmt).one()

        stock_stmt = (
            select(func.count(InventoryBalance.id))
            .join(Warehouse, Warehouse.id == InventoryBalance.warehouse_id)
            .where(
                Warehouse.organization_id == organization_id,
                InventoryBalance.on_hand_quantity - InventoryBalance.reserved_quantity
                <= 5,
            )
        )
        return OperationsDashboard(
            open_order_count=int(order_row.open_order_count or 0),
            ready_to_ship_count=int(order_row.ready_to_ship_count or 0),
            shipped_order_count=int(order_row.shipped_order_count or 0),
            total_order_amount=order_row.total_order_amount,
            low_stock_count=int(self.db.scalar(stock_stmt) or 0),
        )
