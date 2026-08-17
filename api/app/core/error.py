from enum import Enum


class AppErrorKind(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorCode(str, Enum):
    # Auth
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_INVALID_PAYLOAD = "AUTH_INVALID_PAYLOAD"
    AUTH_INVALID_SUBJECT = "AUTH_INVALID_SUBJECT"
    AUTH_INVALID_TYPE = "AUTH_INVALID_TYPE"
    AUTH_MISSING = "AUTH_MISSING"
    AUTH_NOT_FOUND = "AUTH_NOT_FOUND"
    AUTH_TOKEN_REVOKED = "AUTH_TOKEN_REVOKED"
    CURRENT_PASSWORD_INCORRECT = "CURRENT_PASSWORD_INCORRECT"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    MALFORMED_TOKEN = "MALFORMED_TOKEN"
    REFRESH_INVALID = "REFRESH_INVALID"
    REFRESH_INVALID_PAYLOAD = "REFRESH_INVALID_PAYLOAD"
    REFRESH_INVALID_TYPE = "REFRESH_INVALID_TYPE"
    REFRESH_MISSING = "REFRESH_MISSING"
    TOKEN_ALREADY_USED = "TOKEN_ALREADY_USED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # Common
    FORBIDDEN = "FORBIDDEN"
    INVALID_STATE = "INVALID_STATE"
    OPTIMISTIC_LOCK_CONFLICT = "OPTIMISTIC_LOCK_CONFLICT"

    # Accounts
    LOGIN_ID_ALREADY_EXISTS = "LOGIN_ID_ALREADY_EXISTS"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    EMAIL_REQUIRED = "EMAIL_REQUIRED"
    LOGIN_ID_REQUIRED = "LOGIN_ID_REQUIRED"


APP_ERROR_STATUS_CODES = {
    AppErrorKind.BAD_REQUEST: 400,
    AppErrorKind.UNAUTHORIZED: 401,
    AppErrorKind.FORBIDDEN: 403,
    AppErrorKind.NOT_FOUND: 404,
    AppErrorKind.CONFLICT: 409,
    AppErrorKind.INTERNAL_ERROR: 500,
    AppErrorKind.SERVICE_UNAVAILABLE: 503,
}


APP_ERROR_CODE_KINDS: dict[str, AppErrorKind] = {
    ErrorCode.ACCOUNT_DISABLED.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_INVALID.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_PAYLOAD.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_SUBJECT.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_TYPE.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_MISSING.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_NOT_FOUND.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.AUTH_TOKEN_REVOKED.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.CURRENT_PASSWORD_INCORRECT.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.INVALID_CREDENTIALS.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.REFRESH_INVALID.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.REFRESH_INVALID_PAYLOAD.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.REFRESH_INVALID_TYPE.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.REFRESH_MISSING.value: AppErrorKind.UNAUTHORIZED,
    ErrorCode.FORBIDDEN.value: AppErrorKind.FORBIDDEN,
    ErrorCode.ACCOUNT_NOT_FOUND.value: AppErrorKind.NOT_FOUND,
    ErrorCode.EMAIL_ALREADY_EXISTS.value: AppErrorKind.CONFLICT,
    ErrorCode.LOGIN_ID_ALREADY_EXISTS.value: AppErrorKind.CONFLICT,
    ErrorCode.OPTIMISTIC_LOCK_CONFLICT.value: AppErrorKind.CONFLICT,
}


def _normalize_error_code(code: str | Enum) -> str:
    return code.value if isinstance(code, Enum) else str(code)


def _resolve_error_kind(code: str | Enum, kind: AppErrorKind | None) -> AppErrorKind:
    if kind is not None:
        return kind
    return APP_ERROR_CODE_KINDS.get(
        _normalize_error_code(code),
        AppErrorKind.BAD_REQUEST,
    )


class AppError(Exception):
    def __init__(
        self,
        code: str | Enum,
        kind: AppErrorKind | None = None,
        details: dict | None = None,
    ):
        super().__init__(code)
        self.code = _normalize_error_code(code)
        self.kind = _resolve_error_kind(code, kind)
        self.status_code = APP_ERROR_STATUS_CODES[self.kind]
        self.details = details or {}
