from sqlalchemy.orm import Session
from app.module.account.module import AccountModule, Account


class ListAccountsUsecase:
    def __init__(self, db: Session):
        self.module = AccountModule(db)

    def execute(self) -> list[Account]:
        return self.module.get_all()
