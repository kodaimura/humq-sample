from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.query.shipment_overview import ShipmentOverview, ShipmentOverviewQuery
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


class ListShipmentsUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.query = ShipmentOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[ShipmentOverview]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.query.list_by_seller(organization_id)
