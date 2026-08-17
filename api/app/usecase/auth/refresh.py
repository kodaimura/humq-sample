from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.error import AppError, ErrorCode
from app.module.account import AccountModule
from app.core.jwt import create_access_token


@dataclass(frozen=True)
class RefreshInput:
    sub: str
    token_version: int


@dataclass(frozen=True)
class RefreshResult:
    access_token: str


class RefreshUsecase:
    def __init__(self, db: Session):
        self.account_module = AccountModule(db)

    def execute(self, input: RefreshInput) -> RefreshResult:
        if not input.sub or input.token_version is None:
            raise AppError(code=ErrorCode.MALFORMED_TOKEN)

        try:
            account_id = int(input.sub)
        except ValueError:
            raise AppError(code=ErrorCode.AUTH_INVALID_SUBJECT)

        account = self.account_module.get_by_id(account_id)
        if not account:
            raise AppError(code=ErrorCode.AUTH_NOT_FOUND)

        if account.disabled_at is not None:
            raise AppError(code=ErrorCode.ACCOUNT_DISABLED)

        if input.token_version != account.token_version:
            raise AppError(code=ErrorCode.AUTH_TOKEN_REVOKED)

        access_token = create_access_token(
            {
                "sub": input.sub,
                "token_version": input.token_version,
            }
        )
        return RefreshResult(access_token=access_token)
