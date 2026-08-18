from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.procurement import *
from app.usecase.procurement.catalog import ConfigureReorderPolicyInput, ConfigureReorderPolicyUsecase, ConfigureSupplierProductInput, ConfigureSupplierProductUsecase
from app.usecase.procurement.orders import ApprovePurchaseOrderUsecase, CancelPurchaseOrderUsecase, CreatePurchaseOrderInput, CreatePurchaseOrderUsecase, PurchaseOrderLineInput
from app.usecase.procurement.reads import GetPurchaseOrderUsecase, ListPurchaseOrdersUsecase, ListReorderRecommendationsUsecase
from app.usecase.procurement.receipts import CreateGoodsReceiptInput, CreateGoodsReceiptUsecase, GoodsReceiptLineInput, PostGoodsReceiptUsecase


router = APIRouter(tags=["procurement"])


@router.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderDetailsResponse)
def get_purchase_order(purchase_order_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    order, items = GetPurchaseOrderUsecase(db).execute(
        account_id=account_id, purchase_order_id=purchase_order_id
    )
    return ApiResponse.ok(data=PurchaseOrderDetailsResponse(purchase_order=PurchaseOrderResponse.model_validate(order), items=[PurchaseOrderItemResponse.model_validate(item) for item in items]), response=response)


@router.post("/organizations/{organization_id}/supplier-products", response_model=SupplierProductResponse)
def configure_supplier_product(organization_id: int, request: SupplierProductRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ConfigureSupplierProductUsecase(db).execute(ConfigureSupplierProductInput(account_id=account_id, buyer_organization_id=organization_id, **request.model_dump()))
    return ApiResponse.created(data=SupplierProductResponse.model_validate(entity), response=response)


@router.post("/organizations/{organization_id}/reorder-policies", response_model=ReorderPolicyResponse)
def configure_reorder_policy(organization_id: int, request: ReorderPolicyRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ConfigureReorderPolicyUsecase(db).execute(ConfigureReorderPolicyInput(account_id=account_id, organization_id=organization_id, **request.model_dump()))
    return ApiResponse.created(data=ReorderPolicyResponse.model_validate(entity), response=response)


@router.get("/organizations/{organization_id}/reorder-recommendations", response_model=ReorderRecommendationsResponse)
def reorder_recommendations(organization_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    items = ListReorderRecommendationsUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(data=ReorderRecommendationsResponse(recommendations=[ReorderRecommendationResponse.model_validate(item, from_attributes=True) for item in items]), response=response)


@router.get("/organizations/{organization_id}/purchase-orders", response_model=PurchaseOrdersResponse)
def list_purchase_orders(organization_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    items = ListPurchaseOrdersUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(data=PurchaseOrdersResponse(purchase_orders=[PurchaseOrderOverviewResponse.model_validate(item, from_attributes=True) for item in items]), response=response)


@router.post("/organizations/{organization_id}/purchase-orders", response_model=PurchaseOrderOperationResponse)
def create_purchase_order(organization_id: int, request: CreatePurchaseOrderRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CreatePurchaseOrderUsecase(db).execute(CreatePurchaseOrderInput(account_id=account_id, buyer_organization_id=organization_id, supplier_organization_id=request.supplier_organization_id, warehouse_id=request.warehouse_id, expected_date=request.expected_date, note=request.note, items=[PurchaseOrderLineInput(**item.model_dump()) for item in request.items]))
    return ApiResponse.created(data=PurchaseOrderOperationResponse(purchase_order=PurchaseOrderResponse.model_validate(entity)), response=response)


@router.post("/purchase-orders/{purchase_order_id}/approve", response_model=PurchaseOrderOperationResponse)
def approve_purchase_order(purchase_order_id: int, request: ChangeStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ApprovePurchaseOrderUsecase(db).execute(account_id=account_id, purchase_order_id=purchase_order_id, reason=request.reason)
    return ApiResponse.ok(data=PurchaseOrderOperationResponse(purchase_order=PurchaseOrderResponse.model_validate(entity)), response=response)


@router.post("/purchase-orders/{purchase_order_id}/cancel", response_model=PurchaseOrderOperationResponse)
def cancel_purchase_order(purchase_order_id: int, request: ChangeStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CancelPurchaseOrderUsecase(db).execute(account_id=account_id, purchase_order_id=purchase_order_id, reason=request.reason)
    return ApiResponse.ok(data=PurchaseOrderOperationResponse(purchase_order=PurchaseOrderResponse.model_validate(entity)), response=response)


@router.post("/purchase-orders/{purchase_order_id}/receipts", response_model=GoodsReceiptOperationResponse)
def create_goods_receipt(purchase_order_id: int, request: CreateGoodsReceiptRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CreateGoodsReceiptUsecase(db).execute(CreateGoodsReceiptInput(account_id=account_id, purchase_order_id=purchase_order_id, supplier_reference=request.supplier_reference, note=request.note, items=[GoodsReceiptLineInput(**item.model_dump()) for item in request.items]))
    return ApiResponse.created(data=GoodsReceiptOperationResponse(goods_receipt=GoodsReceiptResponse.model_validate(entity)), response=response)


@router.post("/goods-receipts/{goods_receipt_id}/post", response_model=GoodsReceiptOperationResponse)
def post_goods_receipt(goods_receipt_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = PostGoodsReceiptUsecase(db).execute(account_id=account_id, goods_receipt_id=goods_receipt_id)
    return ApiResponse.ok(data=GoodsReceiptOperationResponse(goods_receipt=GoodsReceiptResponse.model_validate(entity)), response=response)
