from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .model import PasswordResetToken


class PasswordResetTokenModule:
    def __init__(self, db: Session):
        self.db = db

    def create(self, entity: PasswordResetToken) -> PasswordResetToken:
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def get_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        return self.db.scalars(stmt).first()

    def find_latest_by_account_id(
        self,
        account_id: int,
    ) -> Optional[PasswordResetToken]:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.account_id == account_id)
            .order_by(desc(PasswordResetToken.created_at))
        )
        return self.db.scalars(stmt).first()

    def invalidate_active_tokens(self, account_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.account_id == account_id)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.expires_at > now)
        )
        for token in self.db.scalars(stmt).all():
            token.used_at = now
        self.db.flush()

    def update(self, entity: PasswordResetToken) -> PasswordResetToken:
        self.db.flush()
        return entity
