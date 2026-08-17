from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.organizations import (
    AddAddressRequest,
    AddressResponse,
    CreateAddressResponse,
    CreateOrganizationRequest,
    CreateOrganizationResponse,
    ListAddressesResponse,
    ListOrganizationsResponse,
    OrganizationAccessResponse,
    OrganizationResponse,
)
from app.usecase.organizations.add_address import (
    AddOrganizationAddressInput,
    AddOrganizationAddressUsecase,
    ListOrganizationAddressesUsecase,
)
from app.usecase.organizations.create import (
    CreateOrganizationInput,
    CreateOrganizationUsecase,
)
from app.usecase.organizations.list import ListOrganizationsUsecase


router = APIRouter(tags=["organizations"])


@router.get("/organizations", response_model=ListOrganizationsResponse)
def list_organizations(
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    organizations = ListOrganizationsUsecase(db).execute(account_id)
    data = ListOrganizationsResponse(
        organizations=[
            OrganizationAccessResponse.model_validate(item, from_attributes=True)
            for item in organizations
        ]
    )
    return ApiResponse.ok(data=data, response=response)


@router.post("/organizations", response_model=CreateOrganizationResponse)
def create_organization(
    request: CreateOrganizationRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    organization = CreateOrganizationUsecase(db).execute(
        CreateOrganizationInput(account_id=account_id, **request.model_dump())
    )
    data = CreateOrganizationResponse(
        organization=OrganizationResponse.model_validate(organization)
    )
    return ApiResponse.created(data=data, response=response)


@router.get(
    "/organizations/{organization_id}/addresses",
    response_model=ListAddressesResponse,
)
def list_addresses(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    addresses = ListOrganizationAddressesUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    data = ListAddressesResponse(
        addresses=[AddressResponse.model_validate(item) for item in addresses]
    )
    return ApiResponse.ok(data=data, response=response)


@router.post(
    "/organizations/{organization_id}/addresses",
    response_model=CreateAddressResponse,
)
def add_address(
    organization_id: int,
    request: AddAddressRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    address = AddOrganizationAddressUsecase(db).execute(
        AddOrganizationAddressInput(
            account_id=account_id,
            organization_id=organization_id,
            **request.model_dump(),
        )
    )
    return ApiResponse.created(
        data=CreateAddressResponse(address=AddressResponse.model_validate(address)),
        response=response,
    )
