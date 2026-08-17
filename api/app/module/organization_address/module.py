from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import OrganizationAddress


class OrganizationAddressModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **values) -> OrganizationAddress:
        entity = OrganizationAddress(**values)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, address_id: int) -> OrganizationAddress | None:
        return self.db.get(OrganizationAddress, address_id)

    def list_by_organization(self, organization_id: int) -> list[OrganizationAddress]:
        stmt = select(OrganizationAddress).where(
            OrganizationAddress.organization_id == organization_id
        ).order_by(OrganizationAddress.is_default.desc(), OrganizationAddress.id)
        return list(self.db.scalars(stmt).all())
