from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateOrderItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_organization_id: int
    shipping_address_id: int | None = None
    requested_ship_date: date | None = None
    note: str | None = Field(default=None, max_length=4000)
    items: list[CreateOrderItemRequest] = Field(min_length=1)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    seller_organization_id: int
    customer_organization_id: int
    status: str
    requested_ship_date: date | None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    note: str | None
    confirmed_at: datetime | None
    canceled_at: datetime | None
    created_at: datetime


class OrderOperationResponse(BaseModel):
    order: OrderResponse


class OrderOverviewResponse(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: str
    requested_ship_date: date | None
    total_amount: Decimal
    item_count: int
    ordered_quantity: int
    reserved_quantity: int
    shipped_quantity: int
    created_at: datetime


class OrdersResponse(BaseModel):
    orders: list[OrderOverviewResponse]


class CancelOrderRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class DashboardResponse(BaseModel):
    open_order_count: int
    ready_to_ship_count: int
    shipped_order_count: int
    total_order_amount: Decimal
    low_stock_count: int
