from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.purchase_order import PurchaseOrder, PurchaseOrderModule
from app.module.purchase_order_item import PurchaseOrderItem, PurchaseOrderItemModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class GetPurchaseOrderUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = PurchaseOrderModule(db)
        self.items = PurchaseOrderItemModule(db)

    def execute(
        self, *, account_id: int, purchase_order_id: int
    ) -> tuple[PurchaseOrder, list[PurchaseOrderItem]]:
        order = self.orders.get_by_id(purchase_order_id)
        if not order:
            raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.buyer_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        return order, self.items.list_by_order(order.id)
