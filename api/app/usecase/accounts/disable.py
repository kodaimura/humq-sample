from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule, Account


@dataclass(frozen=True)
class DisableAccountInput:
    account_id: int


class DisableAccountUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.module = AccountModule(db)

    def execute(self, input: DisableAccountInput) -> Account:
        account = self.module.get_by_id(input.account_id)
        if not account:
            raise AppError(code=ErrorCode.ACCOUNT_NOT_FOUND)

        disabled_account = self.module.disable(account)
        self.db.commit()
        return disabled_account
