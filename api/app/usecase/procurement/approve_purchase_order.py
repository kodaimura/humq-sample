from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, PurchaseOrderStatus
from app.module.outbox_event import OutboxEventModule
from app.module.purchase_order import PurchaseOrder, PurchaseOrderModule
from app.module.purchase_order_status_history import PurchaseOrderStatusHistoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ApprovePurchaseOrderUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = PurchaseOrderModule(db)
        self.history = PurchaseOrderStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit = AuditLogModule(db)

    def execute(
        self, *, account_id: int, purchase_order_id: int, reason: str | None = None
    ) -> PurchaseOrder:
        order = self.orders.get_for_update(purchase_order_id)
        if not order:
            raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.buyer_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        if order.status != PurchaseOrderStatus.DRAFT.value:
            raise AppError(code=ErrorCode.INVALID_PURCHASE_ORDER_STATE)
        previous = self.orders.change_status(order, PurchaseOrderStatus.APPROVED.value)
        self.history.create(
            purchase_order_id=order.id,
            from_status=previous,
            to_status=PurchaseOrderStatus.APPROVED.value,
            reason=reason,
            changed_by_account_id=account_id,
        )
        self.outbox.enqueue(
            event_type="purchase_order.approved",
            aggregate_type="purchase_order",
            aggregate_id=order.id,
            payload={
                "purchase_order_id": order.id,
                "status": PurchaseOrderStatus.APPROVED.value,
            },
        )
        self.audit.record(
            actor_account_id=account_id,
            action="purchase_order.approved",
            resource_type="purchase_order",
            resource_id=order.id,
            details={"reason": reason},
        )
        self.db.commit()
        return order
