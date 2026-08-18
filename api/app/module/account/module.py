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

    def create(
        self,
        *,
        login_id: str,
        email: str | None,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> Account:
        entity = Account(
            login_id=login_id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )
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

    def update_profile(
        self,
        entity: Account,
        *,
        login_id: str,
        email: str | None,
        first_name: str,
        last_name: str,
        password_hash: str | None = None,
    ) -> Account:
        entity.login_id = login_id
        entity.email = email
        entity.first_name = first_name
        entity.last_name = last_name
        if password_hash is not None:
            entity.password_hash = password_hash
            entity.token_version += 1
        self.db.flush()
        return entity

    def change_password(self, entity: Account, password_hash: str) -> Account:
        entity.password_hash = password_hash
        entity.token_version += 1
        self.db.flush()
        return entity

    def disable(self, entity: Account) -> Account:
        entity.disabled_at = datetime.now(timezone.utc)
        entity.token_version += 1
        self.db.flush()
        return entity

    def enable(self, entity: Account) -> Account:
        entity.disabled_at = None
        self.db.flush()
        return entity

    def delete(self, entity: Account, soft: bool = True) -> bool:
        if not entity:
            return False

        if soft:
            entity.deleted_at = datetime.now(timezone.utc)
            self.db.flush()
            return True

        self.db.delete(entity)
        return True


__all__ = ["AccountModule", "Account"]
