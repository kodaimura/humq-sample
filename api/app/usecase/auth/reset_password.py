from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.crypto import hash_password, hash_token
from app.core.error import AppError, ErrorCode
from app.module.account import AccountModule
from app.module.password_reset_token import PasswordResetTokenModule
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class ResetPasswordInput:
    token: str
    new_password: str


class ResetPasswordUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.account_module = AccountModule(db)
        self.token_module = PasswordResetTokenModule(db)

    @transactional
    def execute(self, input: ResetPasswordInput) -> None:
        token_hash = hash_token(input.token)
        token = self.token_module.get_by_hash_for_update(token_hash)

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

        self.account_module.change_password(account, hash_password(input.new_password))
        self.token_module.mark_used(token, used_at=now)
