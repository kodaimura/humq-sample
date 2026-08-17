from app.core.config import config
from app.core.error import AppError, ErrorCode


def resolve_login_id(login_id: str | None, email: str | None) -> str:
    if config.AUTH_LOGIN_ID_MODE == "email":
        if not email:
            raise AppError(code=ErrorCode.EMAIL_REQUIRED)
        return email

    if config.AUTH_LOGIN_ID_MODE == "login_id":
        if not login_id:
            raise AppError(code=ErrorCode.LOGIN_ID_REQUIRED)
        return login_id

    raise AppError(code=ErrorCode.INVALID_STATE)
