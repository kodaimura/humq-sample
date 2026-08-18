from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.sales_order import SalesOrderModule
from app.module.sales_return import SalesReturn, SalesReturnModule
from app.module.sales_return_item import SalesReturnItem, SalesReturnItemModule
from app.query.return_eligibility import ReturnEligibilityQuery, ReturnableOrderItem
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class GetSalesReturnUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.returns = SalesReturnModule(db)
        self.items = SalesReturnItemModule(db)

    def execute(
        self, *, account_id: int, sales_return_id: int
    ) -> tuple[SalesReturn, list[SalesReturnItem]]:
        entity = self.returns.get_by_id(sales_return_id)
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
        return entity, self.items.list_by_return(entity.id)


class GetReturnEligibilityUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.orders = SalesOrderModule(db)
        self.query = ReturnEligibilityQuery(db)

    def execute(
        self, *, account_id: int, order_id: int
    ) -> list[ReturnableOrderItem]:
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
