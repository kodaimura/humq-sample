from sqlalchemy.orm import Session

from app.query.organization_access import OrganizationAccessQuery, OrganizationAccessView


class ListOrganizationsUsecase:
    def __init__(self, db: Session):
        self.query = OrganizationAccessQuery(db)

    def execute(self, account_id: int) -> list[OrganizationAccessView]:
        return self.query.list_for_account(account_id)
