from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.module.account.module import AccountModule, Account
from app.core.crypto import verify_password
from app.core.error import AppError, ErrorCode
from app.core.jwt import create_token_pair


@dataclass(frozen=True)
class LoginInput:
    login_id: str
    password: str
    remember_me: bool


@dataclass(frozen=True)
class LoginResult:
    account: Account
    access_token: str
    refresh_token: str


class LoginUsecase:
    def __init__(self, db: Session):
        self.module = AccountModule(db)

    def execute(self, input: LoginInput) -> LoginResult:
        account = self.module.get_by_login_id(input.login_id)

        if not account or not verify_password(input.password, account.password_hash):
            raise AppError(code=ErrorCode.INVALID_CREDENTIALS)

        if account.disabled_at is not None:
            raise AppError(code=ErrorCode.ACCOUNT_DISABLED)

        access_token, refresh_token = create_token_pair(
            account.id,
            account.token_version,
            input.remember_me,
        )

        return LoginResult(
            account=account,
            access_token=access_token,
            refresh_token=refresh_token,
        )
