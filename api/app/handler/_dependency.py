from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error import AppError, ErrorCode
from app.core.jwt import verify_access_token
from app.module.account import AccountModule


def get_account_id(
    request: Request,
    payload: dict = Depends(verify_access_token),
    db: Session = Depends(get_db),
) -> int:
    account_id = _validate_access_token_account(db, payload)
    request.state.account_id = account_id
    return account_id


def _validate_access_token_account(db: Session, payload: dict) -> int:
    sub = payload.get("sub")
    token_version = payload.get("token_version")
    if sub is None or token_version is None:
        raise AppError(code=ErrorCode.AUTH_INVALID_PAYLOAD)

    try:
        account_id = int(sub)
    except ValueError:
        raise AppError(code=ErrorCode.AUTH_INVALID_SUBJECT)

    account = AccountModule(db).get_by_id(account_id)
    if not account:
        raise AppError(code=ErrorCode.AUTH_NOT_FOUND)

    if account.disabled_at is not None:
        raise AppError(code=ErrorCode.ACCOUNT_DISABLED)

    if token_version != account.token_version:
        raise AppError(code=ErrorCode.AUTH_TOKEN_REVOKED)

    return account.id
