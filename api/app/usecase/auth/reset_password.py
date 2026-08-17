from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.crypto import hash_password, hash_token
from app.core.error import AppError, ErrorCode
from app.module.account import AccountModule
from app.module.password_reset_token import PasswordResetTokenModule


@dataclass(frozen=True)
class ResetPasswordInput:
    token: str
    new_password: str


class ResetPasswordUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.account_module = AccountModule(db)
        self.token_module = PasswordResetTokenModule(db)

    def execute(self, input: ResetPasswordInput) -> None:
        token_hash = hash_token(input.token)
        token = self.token_module.get_by_hash(token_hash)

        if not token:
            raise AppError(code=ErrorCode.TOKEN_INVALID)

        if token.used_at is not None:
            raise AppError(code=ErrorCode.TOKEN_ALREADY_USED)

        now = datetime.now(timezone.utc)
        if token.expires_at <= now:
            raise AppError(code=ErrorCode.TOKEN_EXPIRED)

        account = self.account_module.get_by_id(token.account_id)
        if not account:
            raise AppError(code=ErrorCode.ACCOUNT_NOT_FOUND)

        account.password_hash = hash_password(input.new_password)
        account.token_version += 1
        self.account_module.update(account)

        token.used_at = now
        self.token_module.update(token)

        self.db.commit()
