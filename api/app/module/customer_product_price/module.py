from datetime import date
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .model import CustomerProductPrice


class CustomerProductPriceModule:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        customer_organization_id: int,
        product_id: int,
        unit_price: Decimal,
        valid_from: date,
        valid_to: date | None,
    ) -> CustomerProductPrice:
        entity = CustomerProductPrice(
            customer_organization_id=customer_organization_id,
            product_id=product_id,
            unit_price=unit_price,
            valid_from=valid_from,
            valid_to=valid_to,
        )
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def find_effective(
        self, *, customer_organization_id: int, product_id: int, on_date: date
    ) -> CustomerProductPrice | None:
        stmt = (
            select(CustomerProductPrice)
            .where(
                CustomerProductPrice.customer_organization_id
                == customer_organization_id,
                CustomerProductPrice.product_id == product_id,
                CustomerProductPrice.valid_from <= on_date,
                or_(
                    CustomerProductPrice.valid_to.is_(None),
                    CustomerProductPrice.valid_to >= on_date,
                ),
            )
            .order_by(CustomerProductPrice.valid_from.desc())
        )
        return self.db.scalars(stmt).first()
