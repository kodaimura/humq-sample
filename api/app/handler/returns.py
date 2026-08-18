from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.returns import *
from app.module.business_types import MemberRole
from app.module.sales_order import SalesOrderModule
from app.module.sales_return import SalesReturnModule
from app.module.sales_return_item import SalesReturnItemModule
from app.query.return_eligibility import ReturnEligibilityQuery
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase
from app.usecase.returns.receipts import CreateReturnReceiptInput, CreateReturnReceiptUsecase, PostReturnReceiptUsecase, ReturnReceiptLineInput
from app.usecase.returns.requests import ChangeSalesReturnStatusUsecase, CreateSalesReturnInput, CreateSalesReturnUsecase, ReturnLineInput


router = APIRouter(tags=["returns"])


@router.get("/returns/{sales_return_id}", response_model=SalesReturnDetailsResponse)
def get_sales_return(sales_return_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = SalesReturnModule(db).get_by_id(sales_return_id)
    if not entity:
        from app.core.error import AppError, ErrorCode
        raise AppError(code=ErrorCode.SALES_RETURN_NOT_FOUND)
    order = SalesOrderModule(db).get_by_id(entity.order_id)
    assert order is not None
    RequireOrganizationRoleUsecase(db).execute(organization_id=order.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value, MemberRole.WAREHOUSE.value})
    items = SalesReturnItemModule(db).list_by_return(entity.id)
    return ApiResponse.ok(data=SalesReturnDetailsResponse(sales_return=SalesReturnResponse.model_validate(entity), items=[SalesReturnItemResponse.model_validate(item) for item in items]), response=response)


@router.get("/orders/{order_id}/return-eligibility", response_model=ReturnEligibilityResponse)
def return_eligibility(order_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    order = SalesOrderModule(db).get_by_id(order_id)
    if not order:
        from app.core.error import AppError, ErrorCode
        raise AppError(code=ErrorCode.ORDER_NOT_FOUND)
    RequireOrganizationRoleUsecase(db).execute(organization_id=order.seller_organization_id, account_id=account_id, allowed_roles={MemberRole.ADMIN.value, MemberRole.SALES.value, MemberRole.WAREHOUSE.value})
    items = ReturnEligibilityQuery(db).for_order(order.id)
    return ApiResponse.ok(data=ReturnEligibilityResponse(items=[ReturnableOrderItemResponse.model_validate(item, from_attributes=True) for item in items]), response=response)


@router.post("/orders/{order_id}/returns", response_model=SalesReturnOperationResponse)
def create_sales_return(order_id: int, request: CreateSalesReturnRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CreateSalesReturnUsecase(db).execute(CreateSalesReturnInput(account_id=account_id, order_id=order_id, warehouse_id=request.warehouse_id, reason=request.reason, note=request.note, items=[ReturnLineInput(**item.model_dump()) for item in request.items]))
    return ApiResponse.created(data=SalesReturnOperationResponse(sales_return=SalesReturnResponse.model_validate(entity)), response=response)


@router.post("/returns/{sales_return_id}/approve", response_model=SalesReturnOperationResponse)
def approve_return(sales_return_id: int, request: ReturnStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ChangeSalesReturnStatusUsecase(db).execute(account_id=account_id, sales_return_id=sales_return_id, action="approve", reason=request.reason)
    return ApiResponse.ok(data=SalesReturnOperationResponse(sales_return=SalesReturnResponse.model_validate(entity)), response=response)


@router.post("/returns/{sales_return_id}/cancel", response_model=SalesReturnOperationResponse)
def cancel_return(sales_return_id: int, request: ReturnStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ChangeSalesReturnStatusUsecase(db).execute(account_id=account_id, sales_return_id=sales_return_id, action="cancel", reason=request.reason)
    return ApiResponse.ok(data=SalesReturnOperationResponse(sales_return=SalesReturnResponse.model_validate(entity)), response=response)


@router.post("/returns/{sales_return_id}/receipts", response_model=ReturnReceiptOperationResponse)
def create_return_receipt(sales_return_id: int, request: CreateReturnReceiptRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CreateReturnReceiptUsecase(db).execute(CreateReturnReceiptInput(account_id=account_id, sales_return_id=sales_return_id, note=request.note, items=[ReturnReceiptLineInput(**item.model_dump()) for item in request.items]))
    return ApiResponse.created(data=ReturnReceiptOperationResponse(return_receipt=ReturnReceiptResponse.model_validate(entity)), response=response)


@router.post("/return-receipts/{return_receipt_id}/post", response_model=ReturnReceiptOperationResponse)
def post_return_receipt(return_receipt_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = PostReturnReceiptUsecase(db).execute(account_id=account_id, return_receipt_id=return_receipt_id)
    return ApiResponse.ok(data=ReturnReceiptOperationResponse(return_receipt=ReturnReceiptResponse.model_validate(entity)), response=response)
