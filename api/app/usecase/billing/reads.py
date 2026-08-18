from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.query.billing_overview import BillingOverviewQuery, ReceivableSummary
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase


class ListReceivablesUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.query = BillingOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[ReceivableSummary]:
        self.require_role.execute(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value},
        )
        return self.query.receivables(organization_id)
