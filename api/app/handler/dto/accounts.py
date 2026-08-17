from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.handler.dto.constraints import PasswordString, String100, String255


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


class PostAccountRequest(BaseModel):
    login_id: String255 | None = None
    email: EmailStr | None = None
    first_name: String100
    last_name: String100
    password: PasswordString


class PutAccountRequest(BaseModel):
    login_id: String255 | None = None
    email: EmailStr | None = None
    first_name: String100
    last_name: String100
    password: PasswordString | None = None


class PutAccountPasswordRequest(BaseModel):
    old_password: String255
    new_password: PasswordString


class GetAccountsResponse(BaseModel):
    accounts: list[AccountResponse]


class GetCurrentAccountResponse(BaseModel):
    account: AccountResponse


class GetAccountResponse(BaseModel):
    account: AccountResponse


class PostAccountResponse(BaseModel):
    account: AccountResponse


class PutAccountResponse(BaseModel):
    account: AccountResponse


class PutAccountDisableResponse(BaseModel):
    account: AccountResponse


class PutAccountEnableResponse(BaseModel):
    account: AccountResponse
