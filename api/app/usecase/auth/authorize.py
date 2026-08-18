from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.account import AccountModule


class AuthorizeAccessTokenUsecase:
    def __init__(self, db: Session):
        self.accounts = AccountModule(db)

    def execute(self, payload: dict) -> int:
        sub = payload.get("sub")
        token_version = payload.get("token_version")
        if sub is None or token_version is None:
            raise AppError(code=ErrorCode.AUTH_INVALID_PAYLOAD)

        try:
            account_id = int(sub)
        except ValueError as exc:
            raise AppError(code=ErrorCode.AUTH_INVALID_SUBJECT) from exc

        account = self.accounts.get_by_id(account_id)
        if not account:
            raise AppError(code=ErrorCode.AUTH_NOT_FOUND)
        if account.disabled_at is not None:
            raise AppError(code=ErrorCode.ACCOUNT_DISABLED)
        if token_version != account.token_version:
            raise AppError(code=ErrorCode.AUTH_TOKEN_REVOKED)
        return account.id
