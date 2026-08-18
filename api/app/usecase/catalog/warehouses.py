from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.module.warehouse import Warehouse, WarehouseModule
from app.usecase.organizations._operations import RequireOrganizationRoleOperation


@dataclass(frozen=True)
class CreateWarehouseInput:
    account_id: int
    organization_id: int
    code: str
    name: str


class CreateWarehouseUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.require_role = RequireOrganizationRoleOperation(db)
        self.warehouses = WarehouseModule(db)

    def execute(self, input: CreateWarehouseInput) -> Warehouse:
        self.require_role.run(
            organization_id=input.organization_id,
            account_id=input.account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        warehouse = self.warehouses.create(
            organization_id=input.organization_id, code=input.code, name=input.name
        )
        self.db.commit()
        return warehouse


class ListWarehousesUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.warehouses = WarehouseModule(db)

    def execute(self, *, account_id: int, organization_id: int) -> list[Warehouse]:
        self.require_role.run(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={role.value for role in MemberRole},
        )
        return self.warehouses.list_by_organization(organization_id)
