from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import InventoryEventType, MemberRole, TransferStatus
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.inventory_transfer import InventoryTransfer, InventoryTransferModule
from app.module.inventory_transfer_item import InventoryTransferItemModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ReceiveTransferUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.transfers = InventoryTransferModule(db)
        self.items = InventoryTransferItemModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.warehouses = WarehouseModule(db)
        self.require_role = RequireOrganizationRoleOperation(db)

    def execute(self, *, account_id: int, transfer_id: int) -> InventoryTransfer:
        transfer = self.transfers.get_for_update(transfer_id)
        if not transfer:
            raise AppError(code=ErrorCode.TRANSFER_NOT_FOUND)
        destination = self.warehouses.get_by_id(transfer.destination_warehouse_id)
        assert destination is not None
        self.require_role.run(
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
