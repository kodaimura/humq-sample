from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import Product


class ProductModule:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        organization_id: int,
        category_id: int | None,
        sku: str,
        name: str,
        description: str | None,
        unit_price: Decimal,
    ) -> Product:
        entity = Product(
            organization_id=organization_id,
            category_id=category_id,
            sku=sku,
            name=name,
            description=description,
            unit_price=unit_price,
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_by_sku(self, *, organization_id: int, sku: str) -> Product | None:
        stmt = select(Product).where(
            Product.organization_id == organization_id, Product.sku == sku
        )
        return self.db.scalars(stmt).first()

    def list_by_organization(self, organization_id: int) -> list[Product]:
        stmt = select(Product).where(Product.organization_id == organization_id).order_by(Product.sku)
        return list(self.db.scalars(stmt).all())
