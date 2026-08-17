from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule, Account


@dataclass(frozen=True)
class GetAccountInput:
    account_id: int


class GetAccountUsecase:
    def __init__(self, db: Session):
        self.module = AccountModule(db)

    def execute(self, input: GetAccountInput) -> Account:
        account = self.module.get_by_id(input.account_id)
        if not account:
            raise AppError(code=ErrorCode.ACCOUNT_NOT_FOUND)
        return account
