from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.module.invoice.model import Invoice
from app.module.invoice_item.model import InvoiceItem
from app.module.organization.model import Organization
from app.module.sales_order_item.model import SalesOrderItem
from app.module.shipment_item.model import ShipmentItem


@dataclass(frozen=True)
class InvoiceableShipmentItem:
    shipment_item_id: int
    order_item_id: int
    product_id: int
    shipped_quantity: int
    invoiced_quantity: int
    invoiceable_quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class ReceivableSummary:
    customer_organization_id: int
    customer_name: str
    invoice_count: int
    total_invoiced: Decimal
    total_paid: Decimal
    balance_due: Decimal


class BillingOverviewQuery:
    def __init__(self, db: Session):
        self.db = db

    def invoiceable_shipment_items(
        self, shipment_id: int
    ) -> list[InvoiceableShipmentItem]:
        invoiced = (
            select(
                InvoiceItem.shipment_item_id.label("shipment_item_id"),
                func.sum(InvoiceItem.quantity).label("quantity"),
            )
            .where(InvoiceItem.shipment_item_id.is_not(None))
            .group_by(InvoiceItem.shipment_item_id)
            .subquery()
        )
        stmt = (
            select(
                ShipmentItem.id,
                ShipmentItem.order_item_id,
                ShipmentItem.product_id,
                ShipmentItem.quantity,
                func.coalesce(invoiced.c.quantity, 0),
                SalesOrderItem.unit_price,
            )
            .join(SalesOrderItem, SalesOrderItem.id == ShipmentItem.order_item_id)
            .outerjoin(invoiced, invoiced.c.shipment_item_id == ShipmentItem.id)
            .where(ShipmentItem.shipment_id == shipment_id)
            .order_by(ShipmentItem.id)
        )
        return [
            InvoiceableShipmentItem(
                shipment_item_id=row[0],
                order_item_id=row[1],
                product_id=row[2],
                shipped_quantity=int(row[3]),
                invoiced_quantity=int(row[4]),
                invoiceable_quantity=max(int(row[3]) - int(row[4]), 0),
                unit_price=row[5],
            )
            for row in self.db.execute(stmt)
        ]

    def receivables(self, seller_organization_id: int) -> list[ReceivableSummary]:
        stmt = (
            select(
                Invoice.customer_organization_id,
                Organization.name,
                func.count(Invoice.id),
                func.sum(Invoice.total_amount),
                func.sum(Invoice.paid_amount),
                func.sum(Invoice.total_amount - Invoice.paid_amount),
            )
            .join(Organization, Organization.id == Invoice.customer_organization_id)
            .where(
                Invoice.seller_organization_id == seller_organization_id,
                Invoice.status != "VOID",
            )
            .group_by(Invoice.customer_organization_id, Organization.name)
            .order_by(Organization.name)
        )
        return [ReceivableSummary(*row) for row in self.db.execute(stmt)]
