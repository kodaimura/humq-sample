from fastapi import APIRouter

from app.handler.accounts import router as accounts_router
from app.handler.auth import router as auth_router
from app.handler.catalog import router as catalog_router
from app.handler.inventory import router as inventory_router
from app.handler.orders import router as orders_router
from app.handler.organizations import router as organizations_router
from app.handler.shipments import router as shipments_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(accounts_router)
api_router.include_router(organizations_router)
api_router.include_router(catalog_router)
api_router.include_router(inventory_router)
api_router.include_router(orders_router)
api_router.include_router(shipments_router)
