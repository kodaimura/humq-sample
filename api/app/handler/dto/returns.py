from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class SalesReturnLineRequest(BaseModel):
    order_item_id: int
    quantity: int = Field(gt=0)


class CreateSalesReturnRequest(BaseModel):
    warehouse_id: int
    reason: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=2000)
    items: list[SalesReturnLineRequest] = Field(min_length=1)


class SalesReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    return_number: str
    order_id: int
    customer_organization_id: int
    warehouse_id: int
    status: str
    reason: str
    note: str | None
    requested_credit_amount: Decimal
    approved_at: datetime | None
    completed_at: datetime | None


class SalesReturnOperationResponse(BaseModel):
    sales_return: SalesReturnResponse


class SalesReturnItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sales_return_id: int
    order_item_id: int
    product_id: int
    requested_quantity: int
    received_quantity: int
    restocked_quantity: int
    discarded_quantity: int
    unit_credit: Decimal


class SalesReturnDetailsResponse(BaseModel):
    sales_return: SalesReturnResponse
    items: list[SalesReturnItemResponse]


class ReturnStatusRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class ReturnReceiptLineRequest(BaseModel):
    sales_return_item_id: int
    quantity: int = Field(gt=0)
    disposition: str
    condition_note: str | None = Field(default=None, max_length=1000)


class CreateReturnReceiptRequest(BaseModel):
    note: str | None = Field(default=None, max_length=2000)
    items: list[ReturnReceiptLineRequest] = Field(min_length=1)


class ReturnReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    receipt_number: str
    sales_return_id: int
    warehouse_id: int
    status: str
    note: str | None
    posted_at: datetime | None


class ReturnReceiptOperationResponse(BaseModel):
    return_receipt: ReturnReceiptResponse


class ReturnableOrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    shipped_quantity: int
    already_requested_quantity: int
    returnable_quantity: int


class ReturnEligibilityResponse(BaseModel):
    items: list[ReturnableOrderItemResponse]
