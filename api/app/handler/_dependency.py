from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import verify_access_token
from app.usecase.auth.authorize import AuthorizeAccessTokenUsecase


def get_account_id(
    request: Request,
    payload: dict = Depends(verify_access_token),
    db: Session = Depends(get_db),
) -> int:
    account_id = AuthorizeAccessTokenUsecase(db).execute(payload)
    request.state.account_id = account_id
    return account_id
