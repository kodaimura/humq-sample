from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.audit_log import AuditLogModule
from app.module.business_types import MemberRole, SalesReturnStatus
from app.module.outbox_event import OutboxEventModule
from app.module.sales_order import SalesOrderModule
from app.module.sales_return import SalesReturn, SalesReturnModule
from app.module.sales_return_status_history import SalesReturnStatusHistoryModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class CancelSalesReturnUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.returns = SalesReturnModule(db)
        self.orders = SalesOrderModule(db)
        self.history = SalesReturnStatusHistoryModule(db)
        self.outbox = OutboxEventModule(db)
        self.audit = AuditLogModule(db)

    def execute(
        self, *, account_id: int, sales_return_id: int, reason: str | None = None
    ) -> SalesReturn:
        entity = self.returns.get_for_update(sales_return_id)
        if not entity:
            raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
        order = self.orders.get_by_id(entity.order_id)
        assert order is not None
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=account_id,
            allowed_roles={
                MemberRole.ADMIN.value,
                MemberRole.SALES.value,
                MemberRole.WAREHOUSE.value,
            },
        )
        if entity.status not in {
            SalesReturnStatus.REQUESTED.value,
            SalesReturnStatus.APPROVED.value,
        }:
            raise AppError(code=ErrorCode.INVALID_RETURN_STATE)
        previous = self.returns.change_status(entity, SalesReturnStatus.CANCELED.value)
        self.history.create(
            sales_return_id=entity.id,
            from_status=previous,
            to_status=SalesReturnStatus.CANCELED.value,
            reason=reason,
            changed_by_account_id=account_id,
        )
        self.outbox.enqueue(
            event_type="sales_return.canceled",
            aggregate_type="sales_return",
            aggregate_id=entity.id,
            payload={
                "sales_return_id": entity.id,
                "order_id": entity.order_id,
                "status": SalesReturnStatus.CANCELED.value,
            },
        )
        self.audit.record(
            actor_account_id=account_id,
            action="sales_return.canceled",
            resource_type="sales_return",
            resource_id=entity.id,
            details={"reason": reason},
        )
        self.db.commit()
        return entity
