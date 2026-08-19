from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.core.crypto import hash_password, verify_password
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class UpdatePasswordInput:
    account_id: int
    old_password: str
    new_password: str


class UpdatePasswordUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.module = AccountModule(db)

    @transactional
    def execute(self, input: UpdatePasswordInput) -> None:
        account = self.module.get_by_id(input.account_id)
        if not account:
            raise AppError(code=ErrorCode.ACCOUNT_NOT_FOUND)

        if not verify_password(input.old_password, account.password_hash):
            raise AppError(code=ErrorCode.CURRENT_PASSWORD_INCORRECT)

        self.module.change_password(account, hash_password(input.new_password))
