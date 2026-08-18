from dataclasses import dataclass
from datetime import date
import secrets

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import GoodsReceiptStatus, InventoryEventType, MemberRole, PurchaseOrderStatus
from app.module.goods_receipt import GoodsReceipt, GoodsReceiptModule
from app.module.goods_receipt_item import GoodsReceiptItemModule
from app.module.goods_receipt_status_history import GoodsReceiptStatusHistoryModule
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.outbox_event import OutboxEventModule
from app.module.purchase_order import PurchaseOrderModule
from app.module.purchase_order_item import PurchaseOrderItemModule
from app.module.purchase_order_status_history import PurchaseOrderStatusHistoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase.procurement._policies import purchase_order_status


@dataclass(frozen=True)
class GoodsReceiptLineInput:
    purchase_order_item_id: int
    accepted_quantity: int
    rejected_quantity: int
    rejection_reason: str | None = None


@dataclass(frozen=True)
class CreateGoodsReceiptInput:
    account_id: int
    purchase_order_id: int
    supplier_reference: str | None
    note: str | None
    items: list[GoodsReceiptLineInput]


class CreateGoodsReceiptUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.orders = PurchaseOrderModule(db); self.order_items = PurchaseOrderItemModule(db); self.receipts = GoodsReceiptModule(db); self.items = GoodsReceiptItemModule(db); self.history = GoodsReceiptStatusHistoryModule(db)

    def execute(self, input: CreateGoodsReceiptInput) -> GoodsReceipt:
        order = self.orders.get_for_update(input.purchase_order_id)
        if not order: raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.run(organization_id=order.buyer_organization_id, account_id=input.account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value})
        if order.status not in {PurchaseOrderStatus.APPROVED.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value} or not input.items:
            raise AppError(code=ErrorCode.INVALID_PURCHASE_ORDER_STATE)
        receipt = self.receipts.create(receipt_number=_new_receipt_number(), purchase_order_id=order.id, warehouse_id=order.warehouse_id, received_date=date.today(), supplier_reference=input.supplier_reference, note=input.note, received_by_account_id=input.account_id)
        seen: set[int] = set()
        for line in input.items:
            if line.purchase_order_item_id in seen: raise AppError(code=ErrorCode.INVALID_STATE)
            seen.add(line.purchase_order_item_id)
            order_item = self.order_items.get_for_update(line.purchase_order_item_id)
            quantity = line.accepted_quantity + line.rejected_quantity
            if not order_item or order_item.purchase_order_id != order.id: raise AppError(code=ErrorCode.INVALID_STATE)
            if quantity <= 0 or quantity > order_item.remaining_quantity: raise AppError(code=ErrorCode.RECEIPT_QUANTITY_EXCEEDED)
            if line.rejected_quantity > 0 and not line.rejection_reason: raise AppError(code=ErrorCode.INVALID_STATE)
            self.items.create(goods_receipt_id=receipt.id, purchase_order_item_id=order_item.id, product_id=order_item.product_id, quantity=quantity, accepted_quantity=line.accepted_quantity, rejected_quantity=line.rejected_quantity, rejection_reason=line.rejection_reason)
        self.history.create(goods_receipt_id=receipt.id, from_status=None, to_status=GoodsReceiptStatus.DRAFT.value, reason=None, changed_by_account_id=input.account_id)
        self.db.commit(); return receipt


class PostGoodsReceiptUsecase:
    def __init__(self, db: Session):
        self.db = db; self.require_role = RequireOrganizationRoleOperation(db); self.receipts = GoodsReceiptModule(db); self.receipt_items = GoodsReceiptItemModule(db); self.orders = PurchaseOrderModule(db); self.order_items = PurchaseOrderItemModule(db); self.balances = InventoryBalanceModule(db); self.ledger = InventoryLedgerModule(db); self.receipt_history = GoodsReceiptStatusHistoryModule(db); self.order_history = PurchaseOrderStatusHistoryModule(db); self.outbox = OutboxEventModule(db); self.audit = AuditLogModule(db)

    def execute(self, *, account_id: int, goods_receipt_id: int) -> GoodsReceipt:
        receipt = self.receipts.get_for_update(goods_receipt_id)
        if not receipt: raise AppError(code=ErrorCode.GOODS_RECEIPT_NOT_FOUND)
        order = self.orders.get_for_update(receipt.purchase_order_id)
        assert order is not None
        self.require_role.run(organization_id=order.buyer_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value})
        if receipt.status != GoodsReceiptStatus.DRAFT.value or order.status not in {PurchaseOrderStatus.APPROVED.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value}: raise AppError(code=ErrorCode.INVALID_GOODS_RECEIPT_STATE)
        for item in self.receipt_items.list_by_receipt(receipt.id):
            order_item = self.order_items.get_for_update(item.purchase_order_item_id)
            assert order_item is not None
            if not self.order_items.receive(order_item, item.quantity): raise AppError(code=ErrorCode.RECEIPT_QUANTITY_EXCEEDED)
            if item.accepted_quantity:
                balance = self.balances.get_for_update(warehouse_id=receipt.warehouse_id, product_id=item.product_id, create=True)
                assert balance is not None
                self.balances.adjust_on_hand(balance, item.accepted_quantity)
                self.ledger.record(warehouse_id=receipt.warehouse_id, product_id=item.product_id, event_type=InventoryEventType.PURCHASE_RECEIPT.value, on_hand_delta=item.accepted_quantity, reserved_delta=0, on_hand_after=balance.on_hand_quantity, reserved_after=balance.reserved_quantity, reference_type="goods_receipt", reference_id=receipt.id, actor_account_id=account_id)
        previous_receipt = receipt.status; self.receipts.post(receipt)
        self.receipt_history.create(goods_receipt_id=receipt.id, from_status=previous_receipt, to_status=GoodsReceiptStatus.POSTED.value, reason=None, changed_by_account_id=account_id)
        order_items = self.order_items.list_by_order(order.id)
        next_status = purchase_order_status(
            (item.quantity, item.received_quantity) for item in order_items
        )
        if order.status != next_status:
            previous = self.orders.change_status(order, next_status); self.order_history.create(purchase_order_id=order.id, from_status=previous, to_status=next_status, reason=None, changed_by_account_id=account_id)
        self.outbox.enqueue(event_type="goods_receipt.posted", aggregate_type="goods_receipt", aggregate_id=receipt.id, payload={"goods_receipt_id": receipt.id, "purchase_order_id": order.id, "purchase_order_status": next_status})
        self.audit.record(actor_account_id=account_id, action="goods_receipt.posted", resource_type="goods_receipt", resource_id=receipt.id, details={"purchase_order_id": order.id})
        self.db.commit(); return receipt


def _new_receipt_number() -> str:
    return f"GR-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
