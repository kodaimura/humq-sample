from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.query.operations_dashboard import OperationsDashboard, OperationsDashboardQuery
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class GetOperationsDashboardUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.query = OperationsDashboardQuery(db)

    def execute(self, *, account_id: int, organization_id: int) -> OperationsDashboard:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.query.get(organization_id)
