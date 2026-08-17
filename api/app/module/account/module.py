from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .model import Account


class AccountModule:
    def __init__(self, db: Session):
        self.db = db

    def _base_select(self):
        return select(Account).where(Account.deleted_at.is_(None))

    def create(self, entity: Account) -> Account:
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_all(self) -> list[Account]:
        stmt = self._base_select().order_by(Account.id)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, account_id: int) -> Optional[Account]:
        stmt = self._base_select().where(Account.id == account_id)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[Account]:
        stmt = self._base_select().where(Account.email == email)
        return self.db.scalars(stmt).first()

    def get_by_login_id(self, login_id: str) -> Optional[Account]:
        stmt = self._base_select().where(Account.login_id == login_id)
        return self.db.scalars(stmt).first()

    def update(self, entity: Account) -> Account:
        self.db.flush()
        return entity

    def disable(self, entity: Account) -> Account:
        entity.disabled_at = datetime.now(timezone.utc)
        entity.token_version += 1
        return self.update(entity)

    def enable(self, entity: Account) -> Account:
        entity.disabled_at = None
        return self.update(entity)

    def delete(self, entity: Account, soft: bool = True) -> bool:
        if not entity:
            return False

        if soft:
            entity.deleted_at = datetime.now(timezone.utc)
            self.update(entity)
            return True

        self.db.delete(entity)
        return True


__all__ = ["AccountModule", "Account"]
