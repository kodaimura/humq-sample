from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateCategoryRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    code: str
    name: str
    active: bool


class CategoriesResponse(BaseModel):
    categories: list[CategoryResponse]


class CategoryCreatedResponse(BaseModel):
    category: CategoryResponse


class CreateProductRequest(BaseModel):
    category_id: int | None = None
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    unit_price: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    category_id: int | None
    sku: str
    name: str
    description: str | None
    unit_price: Decimal
    active: bool
    created_at: datetime


class ProductsResponse(BaseModel):
    products: list[ProductResponse]


class ProductCreatedResponse(BaseModel):
    product: ProductResponse


class CreateWarehouseRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=150)


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    code: str
    name: str
    active: bool


class WarehousesResponse(BaseModel):
    warehouses: list[WarehouseResponse]


class WarehouseCreatedResponse(BaseModel):
    warehouse: WarehouseResponse
