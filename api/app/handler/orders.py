from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.orders import (
    CancelOrderRequest,
    CreateOrderRequest,
    DashboardResponse,
    OrderOperationResponse,
    OrderOverviewResponse,
    OrderResponse,
    OrdersResponse,
)
from app.usecase.orders.cancel import CancelOrderUsecase
from app.usecase.orders.confirm import ConfirmOrderInput, ConfirmOrderUsecase
from app.usecase.orders.create import (
    CreateOrderInput,
    CreateOrderLineInput,
    CreateOrderUsecase,
)
from app.usecase.orders.get_operations_dashboard import GetOperationsDashboardUsecase
from app.usecase.orders.list_orders import ListOrdersUsecase


router = APIRouter(tags=["orders"])


@router.get(
    "/organizations/{organization_id}/dashboard", response_model=DashboardResponse
)
def get_dashboard(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    dashboard = GetOperationsDashboardUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=DashboardResponse.model_validate(dashboard, from_attributes=True),
        response=response,
    )


@router.get("/organizations/{organization_id}/orders", response_model=OrdersResponse)
def list_orders(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListOrdersUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=OrdersResponse(
            orders=[
                OrderOverviewResponse.model_validate(item, from_attributes=True)
                for item in items
            ]
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/orders", response_model=OrderOperationResponse
)
def create_order(
    organization_id: int,
    request: CreateOrderRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    order = CreateOrderUsecase(db).execute(
        CreateOrderInput(
            account_id=account_id,
            seller_organization_id=organization_id,
            customer_organization_id=request.customer_organization_id,
            shipping_address_id=request.shipping_address_id,
            requested_ship_date=request.requested_ship_date,
            note=request.note,
            items=[CreateOrderLineInput(**item.model_dump()) for item in request.items],
        )
    )
    return ApiResponse.created(
        data=OrderOperationResponse(order=OrderResponse.model_validate(order)),
        response=response,
    )


@router.post("/orders/{order_id}/confirm", response_model=OrderOperationResponse)
def confirm_order(
    order_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    order = ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(account_id=account_id, order_id=order_id)
    )
    return ApiResponse.ok(
        data=OrderOperationResponse(order=OrderResponse.model_validate(order)),
        response=response,
    )


@router.post("/orders/{order_id}/cancel", response_model=OrderOperationResponse)
def cancel_order(
    order_id: int,
    request: CancelOrderRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    order = CancelOrderUsecase(db).execute(
        account_id=account_id, order_id=order_id, reason=request.reason
    )
    return ApiResponse.ok(
        data=OrderOperationResponse(order=OrderResponse.model_validate(order)),
        response=response,
    )
