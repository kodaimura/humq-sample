from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SupplierProductRequest(BaseModel):
    supplier_organization_id: int
    product_id: int
    supplier_sku: str = Field(min_length=1, max_length=80)
    unit_cost: Decimal = Field(gt=0)
    lead_time_days: int = Field(default=0, ge=0)
    minimum_order_quantity: int = Field(default=1, gt=0)


class SupplierProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_organization_id: int
    product_id: int
    supplier_sku: str
    unit_cost: Decimal
    lead_time_days: int
    minimum_order_quantity: int
    active: bool


class ReorderPolicyRequest(BaseModel):
    warehouse_id: int
    product_id: int
    preferred_supplier_organization_id: int | None = None
    reorder_point: int = Field(ge=0)
    target_stock_quantity: int = Field(gt=0)


class ReorderPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    warehouse_id: int
    product_id: int
    preferred_supplier_organization_id: int | None
    reorder_point: int
    target_stock_quantity: int
    active: bool


class ReorderRecommendationResponse(BaseModel):
    policy_id: int
    warehouse_id: int
    warehouse_name: str
    product_id: int
    sku: str
    product_name: str
    supplier_organization_id: int | None
    supplier_name: str | None
    available_quantity: int
    reorder_point: int
    target_stock_quantity: int
    recommended_quantity: int


class ReorderRecommendationsResponse(BaseModel):
    recommendations: list[ReorderRecommendationResponse]


class PurchaseOrderLineRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_cost: Decimal | None = Field(default=None, gt=0)


class CreatePurchaseOrderRequest(BaseModel):
    supplier_organization_id: int
    warehouse_id: int
    expected_date: date | None = None
    note: str | None = Field(default=None, max_length=2000)
    items: list[PurchaseOrderLineRequest] = Field(min_length=1)


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    purchase_order_number: str
    buyer_organization_id: int
    supplier_organization_id: int
    warehouse_id: int
    status: str
    order_date: date
    expected_date: date | None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    note: str | None
    approved_at: datetime | None


class PurchaseOrderOperationResponse(BaseModel):
    purchase_order: PurchaseOrderResponse


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    purchase_order_id: int
    product_id: int
    quantity: int
    received_quantity: int
    unit_cost: Decimal
    subtotal: Decimal


class PurchaseOrderDetailsResponse(BaseModel):
    purchase_order: PurchaseOrderResponse
    items: list[PurchaseOrderItemResponse]


class PurchaseOrderOverviewResponse(BaseModel):
    id: int
    purchase_order_number: str
    supplier_name: str
    warehouse_name: str
    status: str
    line_count: int
    ordered_quantity: int
    received_quantity: int
    total_amount: Decimal


class PurchaseOrdersResponse(BaseModel):
    purchase_orders: list[PurchaseOrderOverviewResponse]


class ChangeStatusRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class GoodsReceiptLineRequest(BaseModel):
    purchase_order_item_id: int
    accepted_quantity: int = Field(ge=0)
    rejected_quantity: int = Field(default=0, ge=0)
    rejection_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_quantity(self):
        if self.accepted_quantity + self.rejected_quantity <= 0:
            raise ValueError("receipt quantity must be positive")
        if self.rejected_quantity and not self.rejection_reason:
            raise ValueError("rejection_reason is required")
        return self


class CreateGoodsReceiptRequest(BaseModel):
    supplier_reference: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=2000)
    items: list[GoodsReceiptLineRequest] = Field(min_length=1)


class GoodsReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    receipt_number: str
    purchase_order_id: int
    warehouse_id: int
    status: str
    received_date: date
    supplier_reference: str | None
    posted_at: datetime | None


class GoodsReceiptOperationResponse(BaseModel):
    goods_receipt: GoodsReceiptResponse
