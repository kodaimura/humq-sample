from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.crypto import hash_token
from app.core.error import AppError, ErrorCode
from app.module.password_reset_token import PasswordResetTokenModule


@dataclass(frozen=True)
class VerifyResetPasswordTokenInput:
    token: str


class VerifyResetPasswordTokenUsecase:
    def __init__(self, db: Session):
        self.token_module = PasswordResetTokenModule(db)

    def execute(self, input: VerifyResetPasswordTokenInput) -> None:
        token_hash = hash_token(input.token)
        token = self.token_module.get_by_hash(token_hash)

        if not token:
            raise AppError(code=ErrorCode.TOKEN_INVALID)

        if token.used_at is not None:
            raise AppError(code=ErrorCode.TOKEN_ALREADY_USED)

        if token.expires_at <= datetime.now(timezone.utc):
            raise AppError(code=ErrorCode.TOKEN_EXPIRED)
