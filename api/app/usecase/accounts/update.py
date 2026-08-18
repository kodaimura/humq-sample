from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.config import config
from app.core.crypto import hash_password
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule, Account
from app.usecase._policies import resolve_login_id


@dataclass(frozen=True)
class UpdateAccountInput:
    account_id: int
    login_id: str | None
    email: str | None
    first_name: str
    last_name: str
    password: str | None


class UpdateAccountUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.module = AccountModule(db)

    def execute(self, input: UpdateAccountInput) -> Account:
        account = self.module.get_by_id(input.account_id)
        if not account:
            raise AppError(code=ErrorCode.ACCOUNT_NOT_FOUND)

        login_id = resolve_login_id(
            input.login_id,
            input.email,
            login_id_mode=config.AUTH_LOGIN_ID_MODE,
        )

        existing_login_id = self.module.get_by_login_id(login_id)
        if existing_login_id and existing_login_id.id != account.id:
            raise AppError(code=ErrorCode.LOGIN_ID_ALREADY_EXISTS)

        if input.email is not None:
            existing_email = self.module.get_by_email(input.email)
            if existing_email and existing_email.id != account.id:
                raise AppError(code=ErrorCode.EMAIL_ALREADY_EXISTS)

        updated_account = self.module.update_profile(
            account,
            login_id=login_id,
            email=input.email,
            first_name=input.first_name,
            last_name=input.last_name,
            password_hash=(
                hash_password(input.password) if input.password is not None else None
            ),
        )
        self.db.commit()
        return updated_account
