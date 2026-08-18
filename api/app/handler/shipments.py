from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.shipments import (
    CreateShipmentRequest,
    ShipmentOperationResponse,
    ShipmentOverviewResponse,
    ShipmentResponse,
    ShipShipmentRequest,
    ShipmentsResponse,
)
from app.usecase.shipments.create import CreateShipmentUsecase
from app.usecase.shipments.list import ListShipmentsUsecase
from app.usecase.shipments.ship import ShipShipmentUsecase


router = APIRouter(tags=["shipments"])


@router.get(
    "/organizations/{organization_id}/shipments", response_model=ShipmentsResponse
)
def list_shipments(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListShipmentsUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=ShipmentsResponse(
            shipments=[
                ShipmentOverviewResponse.model_validate(item, from_attributes=True)
                for item in items
            ]
        ),
        response=response,
    )


@router.post("/orders/{order_id}/shipments", response_model=ShipmentOperationResponse)
def create_shipment(
    order_id: int,
    request: CreateShipmentRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    shipment = CreateShipmentUsecase(db).execute(
        account_id=account_id,
        order_id=order_id,
        warehouse_id=request.warehouse_id,
        note=request.note,
    )
    return ApiResponse.created(
        data=ShipmentOperationResponse(
            shipment=ShipmentResponse.model_validate(shipment)
        ),
        response=response,
    )


@router.post("/shipments/{shipment_id}/ship", response_model=ShipmentOperationResponse)
def ship_shipment(
    shipment_id: int,
    request: ShipShipmentRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    shipment = ShipShipmentUsecase(db).execute(
        account_id=account_id,
        shipment_id=shipment_id,
        tracking_number=request.tracking_number,
    )
    return ApiResponse.ok(
        data=ShipmentOperationResponse(
            shipment=ShipmentResponse.model_validate(shipment)
        ),
        response=response,
    )
