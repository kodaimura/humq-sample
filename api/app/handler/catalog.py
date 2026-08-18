from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.catalog import (
    CategoriesResponse,
    CategoryCreatedResponse,
    CategoryResponse,
    CreateCategoryRequest,
    CreateProductRequest,
    CreateWarehouseRequest,
    ProductCreatedResponse,
    ProductResponse,
    ProductsResponse,
    WarehouseCreatedResponse,
    WarehouseResponse,
    WarehousesResponse,
)
from app.usecase.catalog.categories import (
    CreateCategoryInput,
    CreateCategoryUsecase,
    ListCategoriesUsecase,
)
from app.usecase.catalog.products import (
    CreateProductInput,
    CreateProductUsecase,
    ListProductsUsecase,
)
from app.usecase.catalog.warehouses import (
    CreateWarehouseInput,
    CreateWarehouseUsecase,
    ListWarehousesUsecase,
)


router = APIRouter(tags=["catalog"])


@router.get(
    "/organizations/{organization_id}/product-categories",
    response_model=CategoriesResponse,
)
def list_categories(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListCategoriesUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=CategoriesResponse(
            categories=[CategoryResponse.model_validate(item) for item in items]
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/product-categories",
    response_model=CategoryCreatedResponse,
)
def create_category(
    organization_id: int,
    request: CreateCategoryRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    item = CreateCategoryUsecase(db).execute(
        CreateCategoryInput(
            account_id=account_id,
            organization_id=organization_id,
            **request.model_dump(),
        )
    )
    return ApiResponse.created(
        data=CategoryCreatedResponse(category=CategoryResponse.model_validate(item)),
        response=response,
    )


@router.get(
    "/organizations/{organization_id}/products", response_model=ProductsResponse
)
def list_products(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListProductsUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=ProductsResponse(
            products=[ProductResponse.model_validate(item) for item in items]
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/products", response_model=ProductCreatedResponse
)
def create_product(
    organization_id: int,
    request: CreateProductRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    item = CreateProductUsecase(db).execute(
        CreateProductInput(
            account_id=account_id,
            organization_id=organization_id,
            **request.model_dump(),
        )
    )
    return ApiResponse.created(
        data=ProductCreatedResponse(product=ProductResponse.model_validate(item)),
        response=response,
    )


@router.get(
    "/organizations/{organization_id}/warehouses", response_model=WarehousesResponse
)
def list_warehouses(
    organization_id: int,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    items = ListWarehousesUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(
        data=WarehousesResponse(
            warehouses=[WarehouseResponse.model_validate(item) for item in items]
        ),
        response=response,
    )


@router.post(
    "/organizations/{organization_id}/warehouses",
    response_model=WarehouseCreatedResponse,
)
def create_warehouse(
    organization_id: int,
    request: CreateWarehouseRequest,
    response: Response,
    account_id: int = Depends(get_account_id),
    db: Session = Depends(get_db),
):
    item = CreateWarehouseUsecase(db).execute(
        CreateWarehouseInput(
            account_id=account_id,
            organization_id=organization_id,
            **request.model_dump(),
        )
    )
    return ApiResponse.created(
        data=WarehouseCreatedResponse(warehouse=WarehouseResponse.model_validate(item)),
        response=response,
    )
