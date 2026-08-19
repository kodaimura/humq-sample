from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.inventory_transfer import InventoryTransfer, InventoryTransferModule
from app.module.inventory_transfer_item import InventoryTransferItemModule
from app.module.product import ProductModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class TransferLineInput:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class CreateTransferInput:
    account_id: int
    organization_id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    note: str | None
    items: list[TransferLineInput]


class CreateTransferUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.warehouses = WarehouseModule(db)
        self.products = ProductModule(db)
        self.transfers = InventoryTransferModule(db)
        self.items = InventoryTransferItemModule(db)

    @transactional
    def execute(self, input: CreateTransferInput) -> InventoryTransfer:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if (
            input.source_warehouse_id == input.destination_warehouse_id
            or not input.items
        ):
            raise AppError(code=ErrorCode.INVALID_TRANSFER_STATE)
        for warehouse_id in (input.source_warehouse_id, input.destination_warehouse_id):
            warehouse = self.warehouses.get_by_id(warehouse_id)
            if not warehouse or warehouse.organization_id != input.organization_id:
                raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        transfer = self.transfers.create(
            source_warehouse_id=input.source_warehouse_id,
            destination_warehouse_id=input.destination_warehouse_id,
            note=input.note,
            created_by_account_id=input.account_id,
        )
        for item in input.items:
            product = self.products.get_by_id(item.product_id)
            if not product or product.organization_id != input.organization_id:
                raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
            if item.quantity <= 0:
                raise AppError(code=ErrorCode.INVALID_TRANSFER_STATE)
            self.items.create(
                transfer_id=transfer.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
        return transfer
