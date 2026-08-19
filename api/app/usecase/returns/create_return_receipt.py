import secrets
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import (
    MemberRole,
    ReturnDisposition,
    SalesReturnStatus,
)
from app.module.return_receipt import ReturnReceipt, ReturnReceiptModule
from app.module.return_receipt_item import ReturnReceiptItemModule
from app.module.sales_order import SalesOrderModule
from app.module.sales_return import SalesReturnModule
from app.module.sales_return_item import SalesReturnItemModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


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
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.returns = SalesReturnModule(db)
        self.orders = SalesOrderModule(db)
        self.return_items = SalesReturnItemModule(db)
        self.receipts = ReturnReceiptModule(db)
        self.receipt_items = ReturnReceiptItemModule(db)

    @transactional
    def execute(self, input: CreateReturnReceiptInput) -> ReturnReceipt:
        sales_return = self.returns.get_for_update(input.sales_return_id)
        if not sales_return:
            raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
        order = self.orders.get_by_id(sales_return.order_id)
        if order is None:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if (
            sales_return.status
            not in {
                SalesReturnStatus.APPROVED.value,
                SalesReturnStatus.PARTIALLY_RECEIVED.value,
            }
            or not input.items
        ):
            raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        entity = self.receipts.create(
            receipt_number=_new_return_receipt_number(),
            sales_return_id=sales_return.id,
            warehouse_id=sales_return.warehouse_id,
            note=input.note,
            received_by_account_id=input.account_id,
        )
        seen: set[int] = set()
        for line in input.items:
            if line.sales_return_item_id in seen or line.disposition not in {
                ReturnDisposition.RESTOCK.value,
                ReturnDisposition.DISCARD.value,
            }:
                raise AppError(code=ErrorCode.INVALID_STATE)
            seen.add(line.sales_return_item_id)
            return_item = self.return_items.get_for_update(line.sales_return_item_id)
            if (
                not return_item
                or return_item.sales_return_id != sales_return.id
                or line.quantity <= 0
                or line.quantity > return_item.remaining_quantity
            ):
                raise AppError(code=ErrorCode.RETURN_QUANTITY_EXCEEDED)
            self.receipt_items.create(
                return_receipt_id=entity.id,
                sales_return_item_id=return_item.id,
                product_id=return_item.product_id,
                quantity=line.quantity,
                disposition=line.disposition,
                condition_note=line.condition_note,
            )
        return entity


def _new_return_receipt_number() -> str:
    return f"RR-{date.today():%Y%m%d}-{secrets.token_hex(3).upper()}"
