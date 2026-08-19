import secrets
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import (
    GoodsReceiptStatus,
    MemberRole,
    PurchaseOrderStatus,
)
from app.module.goods_receipt import GoodsReceipt, GoodsReceiptModule
from app.module.goods_receipt_item import GoodsReceiptItemModule
from app.module.goods_receipt_status_history import GoodsReceiptStatusHistoryModule
from app.module.purchase_order import PurchaseOrderModule
from app.module.purchase_order_item import PurchaseOrderItemModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


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
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = PurchaseOrderModule(db)
        self.order_items = PurchaseOrderItemModule(db)
        self.receipts = GoodsReceiptModule(db)
        self.items = GoodsReceiptItemModule(db)
        self.history = GoodsReceiptStatusHistoryModule(db)

    @transactional
    def execute(self, input: CreateGoodsReceiptInput) -> GoodsReceipt:
        order = self.orders.get_for_update(input.purchase_order_id)
        if not order:
            raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.buyer_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if (
            order.status
            not in {
                PurchaseOrderStatus.APPROVED.value,
                PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
            }
            or not input.items
        ):
            raise AppError(code=ErrorCode.INVALID_PURCHASE_ORDER_STATE)
        receipt = self.receipts.create(
            receipt_number=_new_receipt_number(),
            purchase_order_id=order.id,
            warehouse_id=order.warehouse_id,
            received_date=date.today(),
            supplier_reference=input.supplier_reference,
            note=input.note,
            received_by_account_id=input.account_id,
        )
        seen: set[int] = set()
        for line in input.items:
            if line.purchase_order_item_id in seen:
                raise AppError(code=ErrorCode.INVALID_STATE)
            seen.add(line.purchase_order_item_id)
            order_item = self.order_items.get_for_update(line.purchase_order_item_id)
            quantity = line.accepted_quantity + line.rejected_quantity
            if not order_item or order_item.purchase_order_id != order.id:
                raise AppError(code=ErrorCode.INVALID_STATE)
            if quantity <= 0 or quantity > order_item.remaining_quantity:
                raise AppError(code=ErrorCode.RECEIPT_QUANTITY_EXCEEDED)
            if line.rejected_quantity > 0 and not line.rejection_reason:
                raise AppError(code=ErrorCode.INVALID_STATE)
            self.items.create(
                goods_receipt_id=receipt.id,
                purchase_order_item_id=order_item.id,
                product_id=order_item.product_id,
                quantity=quantity,
                accepted_quantity=line.accepted_quantity,
                rejected_quantity=line.rejected_quantity,
                rejection_reason=line.rejection_reason,
            )
        self.history.create(
            goods_receipt_id=receipt.id,
            from_status=None,
            to_status=GoodsReceiptStatus.DRAFT.value,
            reason=None,
            changed_by_account_id=input.account_id,
        )
        return receipt


def _new_receipt_number() -> str:
    return f"GR-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
