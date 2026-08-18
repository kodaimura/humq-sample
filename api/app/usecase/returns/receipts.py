from dataclasses import dataclass
from datetime import date
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import InventoryEventType, MemberRole, ReturnDisposition, ReturnReceiptStatus, SalesReturnStatus
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.outbox_event import OutboxEventModule
from app.module.return_receipt import ReturnReceipt, ReturnReceiptModule
from app.module.return_receipt_item import ReturnReceiptItemModule
from app.module.sales_order import SalesOrderModule
from app.module.sales_return import SalesReturnModule
from app.module.sales_return_item import SalesReturnItemModule
from app.module.sales_return_status_history import SalesReturnStatusHistoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase.returns._policies import return_status


@dataclass(frozen=True)
class ReturnReceiptLineInput:
    sales_return_item_id: int
    quantity: int
    disposition: str
    condition_note: str | None = None


@dataclass(frozen=True)
class CreateReturnReceiptInput:
    account_id: int
    sales_return_id: int
    note: str | None
    items: list[ReturnReceiptLineInput]


class CreateReturnReceiptUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.returns = SalesReturnModule(db); self.orders = SalesOrderModule(db); self.return_items = SalesReturnItemModule(db); self.receipts = ReturnReceiptModule(db); self.receipt_items = ReturnReceiptItemModule(db)

    def execute(self, input: CreateReturnReceiptInput) -> ReturnReceipt:
        sales_return = self.returns.get_for_update(input.sales_return_id)
        if not sales_return: raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
        order = self.orders.get_by_id(sales_return.order_id); assert order is not None
        self.require_role.run(organization_id=order.seller_organization_id, account_id=input.account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value})
        if sales_return.status not in {SalesReturnStatus.APPROVED.value, SalesReturnStatus.PARTIALLY_RECEIVED.value} or not input.items: raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        entity = self.receipts.create(receipt_number=_new_return_receipt_number(), sales_return_id=sales_return.id, warehouse_id=sales_return.warehouse_id, note=input.note, received_by_account_id=input.account_id)
        seen: set[int] = set()
        for line in input.items:
            if line.sales_return_item_id in seen or line.disposition not in {ReturnDisposition.RESTOCK.value, ReturnDisposition.DISCARD.value}: raise AppError(code=ErrorCode.INVALID_STATE)
            seen.add(line.sales_return_item_id)
            return_item = self.return_items.get_for_update(line.sales_return_item_id)
            if not return_item or return_item.sales_return_id != sales_return.id or line.quantity <= 0 or line.quantity > return_item.remaining_quantity: raise AppError(code=ErrorCode.RETURN_QUANTITY_EXCEEDED)
            self.receipt_items.create(return_receipt_id=entity.id, sales_return_item_id=return_item.id, product_id=return_item.product_id, quantity=line.quantity, disposition=line.disposition, condition_note=line.condition_note)
        self.db.commit(); return entity


class PostReturnReceiptUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.receipts = ReturnReceiptModule(db); self.receipt_items = ReturnReceiptItemModule(db); self.returns = SalesReturnModule(db); self.return_items = SalesReturnItemModule(db); self.orders = SalesOrderModule(db); self.balances = InventoryBalanceModule(db); self.ledger = InventoryLedgerModule(db); self.history = SalesReturnStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, return_receipt_id: int) -> ReturnReceipt:
        receipt = self.receipts.get_for_update(return_receipt_id)
        if not receipt: raise AppError(code=ErrorCode.RETURN_RECEIPT_NOT_FOUND)
        sales_return = self.returns.get_for_update(receipt.sales_return_id); assert sales_return is not None
        order = self.orders.get_by_id(sales_return.order_id); assert order is not None
        self.require_role.run(organization_id=order.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value})
        if receipt.status != ReturnReceiptStatus.DRAFT.value or sales_return.status not in {SalesReturnStatus.APPROVED.value, SalesReturnStatus.PARTIALLY_RECEIVED.value}: raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        for item in self.receipt_items.list_by_receipt(receipt.id):
            return_item = self.return_items.get_for_update(item.sales_return_item_id); assert return_item is not None
            restocked = item.quantity if item.disposition == ReturnDisposition.RESTOCK.value else 0
            discarded = item.quantity - restocked
            if not self.return_items.receive(return_item, quantity=item.quantity, restocked=restocked, discarded=discarded): raise AppError(code=ErrorCode.RETURN_QUANTITY_EXCEEDED)
            if restocked:
                balance = self.balances.get_for_update(warehouse_id=receipt.warehouse_id, product_id=item.product_id, create=True); assert balance is not None
                self.balances.adjust_on_hand(balance, restocked)
                self.ledger.record(warehouse_id=receipt.warehouse_id, product_id=item.product_id, event_type=InventoryEventType.RETURN_RESTOCK.value, on_hand_delta=restocked, reserved_delta=0, on_hand_after=balance.on_hand_quantity, reserved_after=balance.reserved_quantity, reference_type="return_receipt", reference_id=receipt.id, actor_account_id=account_id)
            if discarded:
                balance = self.balances.get_for_update(warehouse_id=receipt.warehouse_id, product_id=item.product_id, create=True); assert balance is not None
                self.ledger.record(warehouse_id=receipt.warehouse_id, product_id=item.product_id, event_type=InventoryEventType.RETURN_DISCARD.value, on_hand_delta=0, reserved_delta=0, on_hand_after=balance.on_hand_quantity, reserved_after=balance.reserved_quantity, reference_type="return_receipt", reference_id=receipt.id, actor_account_id=account_id)
        self.receipts.post(receipt)
        all_items = self.return_items.list_by_return(sales_return.id)
        target = return_status(
            (item.requested_quantity, item.received_quantity) for item in all_items
        )
        if sales_return.status != target:
            previous = self.returns.change_status(sales_return, target); self.history.create(sales_return_id=sales_return.id, from_status=previous, to_status=target, reason=None, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="return_receipt.posted", aggregate_type="return_receipt", aggregate_id=receipt.id, payload={"return_receipt_id": receipt.id, "sales_return_id": sales_return.id, "status": target})
        self.audit.record(actor_account_id=account_id, action="return_receipt.posted", resource_type="return_receipt", resource_id=receipt.id, details={"sales_return_id": sales_return.id})
        self.db.commit(); return receipt


def _new_return_receipt_number() -> str:
    return f"RR-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
