from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import config
from app.core.crypto import generate_token, hash_token
from app.core.mailer import get_mailer
from app.module.account import AccountModule
from app.module.password_reset_token import (
    PasswordResetTokenModule,
)
from app.usecase._transaction import transactional


@dataclass(frozen=True)
class ForgotPasswordInput:
    email: str


class ForgotPasswordUsecase:
    def __init__(self, db: Session):
        self.db = db
        self.account_module = AccountModule(db)
        self.token_module = PasswordResetTokenModule(db)

    @transactional
    def execute(self, input: ForgotPasswordInput) -> None:
        account = self.account_module.get_by_email(input.email)

        if not account or account.disabled_at is not None:
            return

        now = datetime.now(timezone.utc)
        latest = self.token_module.find_latest_by_account_id(account.id)
        resend_after = now - timedelta(
            minutes=config.PASSWORD_RESET_RESEND_INTERVAL_MINUTES
        )
        if latest and latest.created_at > resend_after:
            return

        self.token_module.invalidate_active_tokens(account.id)

        raw_token = generate_token()
        token_hash = hash_token(raw_token)
        expires_at = now + timedelta(
            minutes=config.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES
        )

        self.token_module.create(
            account_id=account.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        reset_url = _build_reset_url(raw_token)
        body = _build_mail_body(
            name=f"{account.last_name} {account.first_name}",
            reset_url=reset_url,
            expires_minutes=config.PASSWORD_RESET_TOKEN_EXPIRES_MINUTES,
        )

        get_mailer().send(
            to=account.email,
            subject="Password reset",
            body=body,
        )


def _build_reset_url(token: str) -> str:
    separator = "&" if "?" in config.PASSWORD_RESET_URL_BASE else "?"
    return f"{config.PASSWORD_RESET_URL_BASE}{separator}{urlencode({'token': token})}"


def _build_mail_body(name: str, reset_url: str, expires_minutes: int) -> str:
    return "\n".join(
        [
            f"Hello {name},",
            "",
            "We received a request to reset your password.",
            "Open the link below to set a new password.",
            "",
            reset_url,
            "",
            f"This link expires in {expires_minutes} minutes.",
            "If you did not request this, you can ignore this email.",
        ]
    )
