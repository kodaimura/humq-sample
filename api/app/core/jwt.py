from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import uuid4

import jwt
from fastapi import Cookie, Header
from jwt import InvalidTokenError

from app.core.config import config
from app.core.error import AppError, ErrorCode

ALGORITHM = "HS256"


def create_access_token(data: dict) -> str:
    if "sub" not in data or "token_version" not in data:
        raise ValueError("sub and token_version are required")
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=config.ACCESS_TOKEN_EXPIRES_SECONDS
    )
    to_encode.update(
        {
            "exp": expire,
            "type": "access",
            "jti": str(uuid4()),
        }
    )
    return jwt.encode(to_encode, config.ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: dict, remember_me: bool = False) -> str:
    if "sub" not in data or "token_version" not in data:
        raise ValueError("sub and token_version are required")
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])
    seconds = (
        config.REFRESH_TOKEN_REMEMBER_ME_EXPIRES_SECONDS
        if remember_me
        else config.REFRESH_TOKEN_EXPIRES_SECONDS
    )
    expire = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "jti": str(uuid4()),
        }
    )
    return jwt.encode(to_encode, config.REFRESH_TOKEN_SECRET, algorithm=ALGORITHM)


def create_token_pair(
    account_id: int | str,
    token_version: int,
    remember_me: bool = False,
) -> Tuple[str, str]:
    data = {
        "sub": str(account_id),
        "token_version": token_version,
    }
    return create_access_token(data), create_refresh_token(data, remember_me)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.ACCESS_TOKEN_SECRET, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.REFRESH_TOKEN_SECRET, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None


def verify_access_token(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(code=ErrorCode.AUTH_MISSING)

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)

    if not payload:
        raise AppError(code=ErrorCode.AUTH_INVALID)

    if payload.get("type") != "access":
        raise AppError(code=ErrorCode.AUTH_INVALID_TYPE)

    if "sub" not in payload or "token_version" not in payload:
        raise AppError(code=ErrorCode.AUTH_INVALID_PAYLOAD)

    return payload


def verify_refresh_token(refresh_token: Optional[str] = Cookie(None)) -> dict:
    if not refresh_token:
        raise AppError(code=ErrorCode.REFRESH_MISSING)

    payload = decode_refresh_token(refresh_token)

    if not payload:
        raise AppError(code=ErrorCode.REFRESH_INVALID)

    if payload.get("type") != "refresh":
        raise AppError(code=ErrorCode.REFRESH_INVALID_TYPE)

    if "sub" not in payload or "token_version" not in payload:
        raise AppError(code=ErrorCode.REFRESH_INVALID_PAYLOAD)

    return payload
