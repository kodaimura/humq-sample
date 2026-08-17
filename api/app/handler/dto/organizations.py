from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OrganizationKindValue = Literal["INTERNAL", "CUSTOMER", "SUPPLIER"]
AddressKindValue = Literal["BILLING", "SHIPPING"]


class CreateOrganizationRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=200)
    kind: OrganizationKindValue
    note: str | None = Field(default=None, max_length=2000)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    kind: str
    status: str
    created_at: datetime


class OrganizationAccessResponse(BaseModel):
    organization_id: int
    code: str
    name: str
    kind: str
    status: str
    role: str


class CreateOrganizationResponse(BaseModel):
    organization: OrganizationResponse


class ListOrganizationsResponse(BaseModel):
    organizations: list[OrganizationAccessResponse]


class AddAddressRequest(BaseModel):
    kind: AddressKindValue = "SHIPPING"
    name: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    prefecture: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address_line1: str = Field(min_length=1, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    recipient_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    is_default: bool = False


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    kind: str
    name: str
    postal_code: str
    prefecture: str
    city: str
    address_line1: str
    address_line2: str | None
    recipient_name: str
    phone: str | None
    is_default: bool


class CreateAddressResponse(BaseModel):
    address: AddressResponse


class ListAddressesResponse(BaseModel):
    addresses: list[AddressResponse]
