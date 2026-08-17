from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.handler.dto.constraints import (
    PasswordString,
    String100,
    String255,
    TokenString,
)


# ==============================
# Request DTO
# ==============================


class SignupRequest(BaseModel):
    login_id: String255 | None = None
    email: EmailStr | None = None
    first_name: String100
    last_name: String100
    password: PasswordString


class LoginRequest(BaseModel):
    login_id: String255
    password: String255
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: TokenString
    new_password: PasswordString


# ==============================
# Response DTO
# ==============================


class AccountResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    login_id: str
    first_name: str
    last_name: str
    disabled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignupResponse(BaseModel):
    account: AccountResponse


class LoginResponse(BaseModel):
    account: AccountResponse
    access_token: str


class RefreshResponse(BaseModel):
    access_token: str
