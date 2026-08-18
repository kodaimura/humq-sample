from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import InventoryEventType, MemberRole
from app.module.inventory_adjustment import (
    InventoryAdjustment,
    InventoryAdjustmentModule,
)
from app.module.inventory_adjustment_item import InventoryAdjustmentItemModule
from app.module.inventory_balance import InventoryBalanceModule
from app.module.inventory_ledger import InventoryLedgerModule
from app.module.product import ProductModule
from app.module.warehouse import WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class AdjustmentLineInput:
    product_id: int
    quantity_delta: int
    note: str | None = None


@dataclass(frozen=True)
class ApplyInventoryAdjustmentInput:
    account_id: int
    organization_id: int
    warehouse_id: int
    reason: str
    items: list[AdjustmentLineInput]


class ApplyInventoryAdjustmentUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.warehouses = WarehouseModule(db)
        self.products = ProductModule(db)
        self.adjustments = InventoryAdjustmentModule(db)
        self.adjustment_items = InventoryAdjustmentItemModule(db)
        self.balances = InventoryBalanceModule(db)
        self.ledger = InventoryLedgerModule(db)
        self.audit_logs = AuditLogModule(db)

    def execute(self, input: ApplyInventoryAdjustmentInput) -> InventoryAdjustment:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        warehouse = self.warehouses.get_by_id(input.warehouse_id)
        if not warehouse or warehouse.organization_id != input.organization_id:
            raise AppError(code=ErrorCode.WAREHOUSE_NOT_FOUND)
        if not input.items or any(item.quantity_delta == 0 for item in input.items):
            raise AppError(code=ErrorCode.INVALID_ADJUSTMENT)

        adjustment = self.adjustments.create(
            warehouse_id=input.warehouse_id,
            reason=input.reason,
            created_by_account_id=input.account_id,
        )
        for item in input.items:
            product = self.products.get_by_id(item.product_id)
            if not product or product.organization_id != input.organization_id:
                raise AppError(code=ErrorCode.PRODUCT_NOT_FOUND)
            adjustment_item = self.adjustment_items.create(
                adjustment_id=adjustment.id,
                product_id=item.product_id,
                quantity_delta=item.quantity_delta,
                note=item.note,
            )
            balance = self.balances.get_for_update(
                warehouse_id=input.warehouse_id,
                product_id=item.product_id,
                create=True,
            )
            assert balance is not None
            if not self.balances.adjust_on_hand(balance, item.quantity_delta):
                raise AppError(
                    code=ErrorCode.INVENTORY_INSUFFICIENT,
                    details={"product_id": item.product_id},
                )
            self.ledger.record(
                warehouse_id=input.warehouse_id,
                product_id=item.product_id,
                event_type=InventoryEventType.ADJUSTMENT.value,
                on_hand_delta=item.quantity_delta,
                reserved_delta=0,
                on_hand_after=balance.on_hand_quantity,
                reserved_after=balance.reserved_quantity,
                reference_type="inventory_adjustment_item",
                reference_id=adjustment_item.id,
                actor_account_id=input.account_id,
            )
        self.adjustments.mark_applied(adjustment)
        self.audit_logs.record(
            actor_account_id=input.account_id,
            action="inventory.adjusted",
            resource_type="inventory_adjustment",
            resource_id=adjustment.id,
            details={
                "warehouse_id": input.warehouse_id,
                "line_count": len(input.items),
            },
        )
        self.db.commit()
        return adjustment
