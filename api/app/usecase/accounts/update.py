from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.crypto import hash_password
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule, Account
from app.usecase.helper import resolve_login_id


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

        login_id = resolve_login_id(input.login_id, input.email)

        existing_login_id = self.module.get_by_login_id(login_id)
        if existing_login_id and existing_login_id.id != account.id:
            raise AppError(code=ErrorCode.LOGIN_ID_ALREADY_EXISTS)

        if input.email is not None:
            existing_email = self.module.get_by_email(input.email)
            if existing_email and existing_email.id != account.id:
                raise AppError(code=ErrorCode.EMAIL_ALREADY_EXISTS)

        account.login_id = login_id
        account.email = input.email
        account.first_name = input.first_name
        account.last_name = input.last_name

        if input.password is not None:
            account.password_hash = hash_password(input.password)
            account.token_version += 1

        updated_account = self.module.update(account)
        self.db.commit()
        return updated_account
