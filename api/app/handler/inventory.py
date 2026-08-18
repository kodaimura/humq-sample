from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.inventory import (
    AdjustmentAppliedResponse,
    AdjustmentResponse,
    ApplyAdjustmentRequest,
    CreateTransferRequest,
    InventoryOverviewResponse,
    InventoryResponse,
    TransferOperationResponse,
    TransferResponse,
)
from app.usecase.inventory.adjust import (
    AdjustmentLineInput,
    ApplyInventoryAdjustmentInput,
    ApplyInventoryAdjustmentUsecase,
)
from app.usecase.inventory.list import ListInventoryUsecase
from app.usecase.inventory.transfer import (
    CreateTransferInput,
    CreateTransferUsecase,
    ReceiveTransferUsecase,
    ShipTransferUsecase,
    TransferLineInput,
)


router = APIRouter(tags=["inventory"])


@router.get(
    "/organizations/{organization_id}/inventory", response_model=InventoryResponse
)
def list_inventory(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListInventoryUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=InventoryResponse(
            inventory=[
                InventoryOverviewResponse.model_validate(item, from_attributes=True)
                for item in items
            ]
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/inventory-adjustments",
    response_model=AdjustmentAppliedResponse,
)
def apply_adjustment(
    organization_id: int,
    request: ApplyAdjustmentRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    adjustment = ApplyInventoryAdjustmentUsecase(db).execute(
        ApplyInventoryAdjustmentInput(
            account_id=account_id,
            organization_id=organization_id,
            warehouse_id=request.warehouse_id,
            reason=request.reason,
            items=[AdjustmentLineInput(**item.model_dump()) for item in request.items],
        )
    )
    return ApiResponse.created(
        data=AdjustmentAppliedResponse(
            adjustment=AdjustmentResponse.model_validate(adjustment)
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/inventory-transfers",
    response_model=TransferOperationResponse,
)
def create_transfer(
    organization_id: int,
    request: CreateTransferRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    transfer = CreateTransferUsecase(db).execute(
        CreateTransferInput(
            account_id=account_id,
            organization_id=organization_id,
            source_warehouse_id=request.source_warehouse_id,
            destination_warehouse_id=request.destination_warehouse_id,
            note=request.note,
            items=[TransferLineInput(**item.model_dump()) for item in request.items],
        )
    )
    return ApiResponse.created(
        data=TransferOperationResponse(
            transfer=TransferResponse.model_validate(transfer)
        ),
        response=response,
    )


@router.post(
    "/inventory-transfers/{transfer_id}/ship", response_model=TransferOperationResponse
)
def ship_transfer(
    transfer_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    transfer = ShipTransferUsecase(db).execute(
        account_id=account_id, transfer_id=transfer_id
    )
    return ApiResponse.ok(
        data=TransferOperationResponse(
            transfer=TransferResponse.model_validate(transfer)
        ),
        response=response,
    )


@router.post(
    "/inventory-transfers/{transfer_id}/receive",
    response_model=TransferOperationResponse,
)
def receive_transfer(
    transfer_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    transfer = ReceiveTransferUsecase(db).execute(
        account_id=account_id, transfer_id=transfer_id
    )
    return ApiResponse.ok(
        data=TransferOperationResponse(
            transfer=TransferResponse.model_validate(transfer)
        ),
        response=response,
    )
