from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import InventoryEventType, MemberRole, TransferStatus
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.inventory_transfer import InventoryTransfer, InventoryTransferModule
from app.module.inventory_transfer_item import InventoryTransferItemModule
from app.module.product import ProductModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase


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
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.warehouses = WarehouseModule(db)
        self.products = ProductModule(db)
        self.transfers = InventoryTransferModule(db)
        self.items = InventoryTransferItemModule(db)

    def execute(self, input: CreateTransferInput) -> InventoryTransfer:
        self.require_role.execute(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if input.source_warehouse_id == input.destination_warehouse_id or not input.items:
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
                transfer_id=transfer.id, product_id=item.product_id, quantity=item.quantity
            )
        self.db.commit()
        return transfer


class ShipTransferUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.transfers = InventoryTransferModule(db)
        self.items = InventoryTransferItemModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.warehouses = WarehouseModule(db)
        self.require_role = RequireOrganizationRoleUsecase(db)

    def execute(self, *, account_id: int, transfer_id: int) -> InventoryTransfer:
        transfer = self.transfers.get_for_update(transfer_id)
        if not transfer:
            raise AppError(code=ErrorCode.TRANSFER_NOT_FOUND)
        source = self.warehouses.get_by_id(transfer.source_warehouse_id)
        assert source is not None
        self.require_role.execute(
            organization_id=source.organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if transfer.status != TransferStatus.DRAFT.value:
            raise AppError(code=ErrorCode.INVALID_TRANSFER_STATE)
        for item in self.items.list_by_transfer(transfer.id):
            balance = self.balances.get_for_update(
                warehouse_id=transfer.source_warehouse_id, product_id=item.product_id
            )
            if not balance or not self.balances.adjust_on_hand(balance, -item.quantity):
                raise AppError(
                    code=ErrorCode.INVENTORY_INSUFFICIENT,
                    details={"product_id": item.product_id},
                )
            self.ledger.record(
                warehouse_id=transfer.source_warehouse_id,
                product_id=item.product_id,
                event_type=InventoryEventType.TRANSFER_OUT.value,
                on_hand_delta=-item.quantity,
                reserved_delta=0,
                on_hand_after=balance.on_hand_quantity,
                reserved_after=balance.reserved_quantity,
                reference_type="inventory_transfer",
                reference_id=transfer.id,
                actor_account_id=account_id,
            )
        self.transfers.mark_in_transit(transfer)
        self.db.commit()
        return transfer


class ReceiveTransferUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.transfers = InventoryTransferModule(db)
        self.items = InventoryTransferItemModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.warehouses = WarehouseModule(db)
        self.require_role = RequireOrganizationRoleUsecase(db)

    def execute(self, *, account_id: int, transfer_id: int) -> InventoryTransfer:
        transfer = self.transfers.get_for_update(transfer_id)
        if not transfer:
            raise AppError(code=ErrorCode.TRANSFER_NOT_FOUND)
        destination = self.warehouses.get_by_id(transfer.destination_warehouse_id)
        assert destination is not None
        self.require_role.execute(
            organization_id=destination.organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if transfer.status != TransferStatus.IN_TRANSIT.value:
            raise AppError(code=ErrorCode.INVALID_TRANSFER_STATE)
        for item in self.items.list_by_transfer(transfer.id):
            balance = self.balances.get_for_update(
                warehouse_id=transfer.destination_warehouse_id,
                product_id=item.product_id,
                create=True,
            )
            assert balance is not None
            self.balances.adjust_on_hand(balance, item.quantity)
            self.ledger.record(
                warehouse_id=transfer.destination_warehouse_id,
                product_id=item.product_id,
                event_type=InventoryEventType.TRANSFER_IN.value,
                on_hand_delta=item.quantity,
                reserved_delta=0,
                on_hand_after=balance.on_hand_quantity,
                reserved_after=balance.reserved_quantity,
                reference_type="inventory_transfer",
                reference_id=transfer.id,
                actor_account_id=account_id,
            )
        self.transfers.mark_received(transfer)
        self.db.commit()
        return transfer
