from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateShipmentRequest(BaseModel):
    warehouse_id: int
    note: str | None = Field(default=None, max_length=2000)


class ShipShipmentRequest(BaseModel):
    tracking_number: str | None = Field(default=None, max_length=100)


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_number: str
    order_id: int
    warehouse_id: int
    status: str
    tracking_number: str | None
    note: str | None
    shipped_at: datetime | None
    created_at: datetime


class ShipmentOperationResponse(BaseModel):
    shipment: ShipmentResponse


class ShipmentOverviewResponse(BaseModel):
    id: int
    shipment_number: str
    order_id: int
    order_number: str
    customer_name: str
    warehouse_name: str
    status: str
    item_count: int
    total_quantity: int
    tracking_number: str | None
    shipped_at: datetime | None
    created_at: datetime


class ShipmentsResponse(BaseModel):
    shipments: list[ShipmentOverviewResponse]
