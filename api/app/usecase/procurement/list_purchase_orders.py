from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.query.procurement_overview import (
    ProcurementOverviewQuery,
    PurchaseOrderOverview,
)
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ListPurchaseOrdersUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.query = ProcurementOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[PurchaseOrderOverview]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        return self.query.purchase_orders(organization_id)
