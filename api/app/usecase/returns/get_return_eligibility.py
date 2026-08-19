from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.sales_order import SalesOrderModule
from app.query.return_eligibility import ReturnEligibilityQuery, ReturnableOrderItem
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class GetReturnEligibilityUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.query = ReturnEligibilityQuery(db)

    def execute(self, *, account_id: int, order_id: int) -> list[ReturnableOrderItem]:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
        self.require_role.run(
            organization_id=order.seller_organization_id,
            account_id=account_id,
            allowed_roles={
                MemberRole.ADMIN.value,
                MemberRole.SALES.value,
                MemberRole.WAREHOUSE.value,
            },
        )
        return self.query.for_order(order.id)
