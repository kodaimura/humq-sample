from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import ProductCategory


class ProductCategoryModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, organization_id: int, code: str, name: str) -> ProductCategory:
        entity = ProductCategory(organization_id=organization_id, code=code, name=name)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, category_id: int) -> ProductCategory | None:
        return self.db.get(ProductCategory, category_id)

    def list_by_organization(self, organization_id: int) -> list[ProductCategory]:
        stmt = (
            select(ProductCategory)
            .where(ProductCategory.organization_id == organization_id)
            .order_by(ProductCategory.name)
        )
        return list(self.db.scalars(stmt).all())
