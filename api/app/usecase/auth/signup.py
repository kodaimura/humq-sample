from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.config import config
from app.core.crypto import hash_password
from app.core.error import AppError, ErrorCode
from app.module.account.module import AccountModule, Account
from app.usecase._policies import resolve_login_id


@dataclass(frozen=True)
class SignupInput:
    login_id: str | None
    email: str | None
    password: str
    first_name: str
    last_name: str


class SignupUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.module = AccountModule(db)

    def execute(self, input: SignupInput) -> Account:
        login_id = resolve_login_id(
            input.login_id,
            input.email,
            login_id_mode=config.AUTH_LOGIN_ID_MODE,
        )

        existing_login_id = self.module.get_by_login_id(login_id)
        if existing_login_id:
            raise AppError(code=ErrorCode.LOGIN_ID_ALREADY_EXISTS)

        if input.email is not None:
            existing_email = self.module.get_by_email(input.email)
            if existing_email:
                raise AppError(code=ErrorCode.EMAIL_ALREADY_EXISTS)

        hashed = hash_password(input.password)
        account = self.module.create(
            Account(
                login_id=login_id,
                email=input.email,
                password_hash=hashed,
                first_name=input.first_name,
                last_name=input.last_name,
            )
        )

        self.db.commit()
        return account
