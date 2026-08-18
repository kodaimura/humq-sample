from dataclasses import dataclass
from datetime import date
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, OrderStatus, SalesReturnStatus
from app.module.outbox_event import OutboxEventModule
from app.module.sales_order import SalesOrderModule
from app.module.sales_order_item import SalesOrderItemModule
from app.module.sales_return import SalesReturn, SalesReturnModule
from app.module.sales_return_item import SalesReturnItemModule
from app.module.sales_return_status_history import SalesReturnStatusHistoryModule
from app.module.warehouse import WarehouseModule
from app.query.return_eligibility import ReturnEligibilityQuery
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase.returns._policies import (
    ReturnEligibility,
    ReturnRequestLine,
    requested_credit,
    validate_return_request,
)


@dataclass(frozen=True)
class ReturnLineInput:
    order_item_id: int
    quantity: int


@dataclass(frozen=True)
class CreateSalesReturnInput:
    account_id: int
    order_id: int
    warehouse_id: int
    reason: str
    note: str | None
    items: list[ReturnLineInput]


class CreateSalesReturnUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.orders = SalesOrderModule(db); self.order_items = SalesOrderItemModule(db); self.warehouses = WarehouseModule(db); self.returns = SalesReturnModule(db); self.return_items = SalesReturnItemModule(db); self.history = SalesReturnStatusHistoryModule(db); self.eligibility = ReturnEligibilityQuery(db); self.audit = AuditLogModule(db)

    def execute(self, input: CreateSalesReturnInput) -> SalesReturn:
        order = self.orders.get_for_update(input.order_id)
        if not order: raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(organization_id=order.seller_organization_id, account_id=input.account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value, MemberRole.WAREHOUSE.value})
        if order.status not in {OrderStatus.SHIPPED.value, OrderStatus.PARTIALLY_SHIPPED.value}: raise AppError(code=ErrorCode.INVALID_ORDER_STATE)
        warehouse = self.warehouses.get_by_id(input.warehouse_id)
        if not warehouse or warehouse.organization_id != order.seller_organization_id: raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        eligible = {item.order_item_id: item for item in self.eligibility.for_order(order.id)}
        order_items = {item.id: item for item in self.order_items.list_by_order(order.id)}
        policy_lines: list[ReturnRequestLine] = []
        for line in input.items:
            eligibility = eligible.get(line.order_item_id); order_item = order_items.get(line.order_item_id)
            if not eligibility or not order_item: raise AppError(code=ErrorCode.RETURN_QUANTITY_EXCEEDED)
            policy_lines.append(
                ReturnRequestLine(
                    order_item_id=order_item.id,
                    requested_quantity=line.quantity,
                    eligibility=ReturnEligibility(
                        shipped_quantity=eligibility.shipped_quantity,
                        previously_requested_quantity=eligibility.already_requested_quantity,
                    ),
                    unit_credit=order_item.unit_price,
                )
            )
        try:
            validated_lines = validate_return_request(policy_lines)
            credit = requested_credit(validated_lines)
        except ValueError as exc:
            raise AppError(code=ErrorCode.RETURN_QUANTITY_EXCEEDED) from exc
        entity = self.returns.create(return_number=_new_return_number(), order_id=order.id, customer_organization_id=order.customer_organization_id, warehouse_id=warehouse.id, reason=input.reason, note=input.note, requested_by_account_id=input.account_id)
        for line in validated_lines:
            order_item = order_items[line.order_item_id]
            self.return_items.create(sales_return_id=entity.id, order_item_id=order_item.id, product_id=order_item.product_id, requested_quantity=line.requested_quantity, unit_credit=order_item.unit_price)
        self.returns.set_requested_credit_amount(entity, credit)
        self.history.create(sales_return_id=entity.id, from_status=None, to_status=SalesReturnStatus.REQUESTED.value, reason=input.reason, changed_by_account_id=input.account_id)
        self.audit.record(actor_account_id=input.account_id, action="sales_return.requested", resource_type="sales_return", resource_id=entity.id, details={"order_id": order.id, "requested_credit_amount": str(credit)})
        self.db.commit(); return entity


class ApproveSalesReturnUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.returns = SalesReturnModule(db); self.orders = SalesOrderModule(db); self.history = SalesReturnStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, sales_return_id: int, reason: str | None = None) -> SalesReturn:
        entity = self.returns.get_for_update(sales_return_id)
        if not entity: raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
        order = self.orders.get_by_id(entity.order_id); assert order is not None
        self.require_role.run(organization_id=order.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value, MemberRole.WAREHOUSE.value})
        if entity.status != SalesReturnStatus.REQUESTED.value: raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        previous = self.returns.change_status(entity, SalesReturnStatus.APPROVED.value)
        self.history.create(sales_return_id=entity.id, from_status=previous, to_status=SalesReturnStatus.APPROVED.value, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="sales_return.approved", aggregate_type="sales_return", aggregate_id=entity.id, payload={"sales_return_id": entity.id, "order_id": entity.order_id, "status": SalesReturnStatus.APPROVED.value})
        self.audit.record(actor_account_id=account_id, action="sales_return.approved", resource_type="sales_return", resource_id=entity.id, details={"reason": reason})
        self.db.commit(); return entity


class CancelSalesReturnUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.returns = SalesReturnModule(db); self.orders = SalesOrderModule(db); self.history = SalesReturnStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, sales_return_id: int, reason: str | None = None) -> SalesReturn:
        entity = self.returns.get_for_update(sales_return_id)
        if not entity: raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
        order = self.orders.get_by_id(entity.order_id); assert order is not None
        self.require_role.run(organization_id=order.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value, MemberRole.WAREHOUSE.value})
        if entity.status not in {SalesReturnStatus.REQUESTED.value, SalesReturnStatus.APPROVED.value}: raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        previous = self.returns.change_status(entity, SalesReturnStatus.CANCELED.value)
        self.history.create(sales_return_id=entity.id, from_status=previous, to_status=SalesReturnStatus.CANCELED.value, reason=reason, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="sales_return.canceled", aggregate_type="sales_return", aggregate_id=entity.id, payload={"sales_return_id": entity.id, "order_id": entity.order_id, "status": SalesReturnStatus.CANCELED.value})
        self.audit.record(actor_account_id=account_id, action="sales_return.canceled", resource_type="sales_return", resource_id=entity.id, details={"reason": reason})
        self.db.commit(); return entity


def _new_return_number() -> str:
    return f"RT-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
