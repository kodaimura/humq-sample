from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryOverviewResponse(BaseModel):
    balance_id: int
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    product_id: int
    sku: str
    product_name: str
    on_hand_quantity: int
    reserved_quantity: int
    available_quantity: int


class InventoryResponse(BaseModel):
    inventory: list[InventoryOverviewResponse]


class AdjustmentItemRequest(BaseModel):
    product_id: int
    quantity_delta: int = Field(ne=0)
    note: str | None = Field(default=None, max_length=1000)


class ApplyAdjustmentRequest(BaseModel):
    warehouse_id: int
    reason: str = Field(min_length=1, max_length=2000)
    items: list[AdjustmentItemRequest] = Field(min_length=1)


class AdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_id: int
    status: str
    reason: str
    applied_at: datetime | None


class AdjustmentAppliedResponse(BaseModel):
    adjustment: AdjustmentResponse


class TransferItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CreateTransferRequest(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    note: str | None = Field(default=None, max_length=2000)
    items: list[TransferItemRequest] = Field(min_length=1)


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    status: str
    note: str | None
    shipped_at: datetime | None
    received_at: datetime | None


class TransferOperationResponse(BaseModel):
    transfer: TransferResponse
