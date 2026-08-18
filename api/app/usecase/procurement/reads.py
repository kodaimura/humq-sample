from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.module.business_types import MemberRole
from app.module.purchase_order import PurchaseOrder, PurchaseOrderModule
from app.module.purchase_order_item import PurchaseOrderItem, PurchaseOrderItemModule
from app.query.procurement_overview import ProcurementOverviewQuery, PurchaseOrderOverview
from app.usecase.organizations.require_role import RequireOrganizationRoleUsecase
from app.usecase.procurement.policies import reorder_decision


@dataclass(frozen=True)
class ReorderRecommendation:
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


class GetPurchaseOrderUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.orders = PurchaseOrderModule(db)
        self.items = PurchaseOrderItemModule(db)

    def execute(
        self, *, account_id: int, purchase_order_id: int
    ) -> tuple[PurchaseOrder, list[PurchaseOrderItem]]:
        order = self.orders.get_by_id(purchase_order_id)
        if not order:
            raise AppError(code=ErrorCode.PURCHASE_ORDER_NOT_FOUND)
        self.require_role.execute(
            organization_id=order.buyer_organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        return order, self.items.list_by_order(order.id)


class ListPurchaseOrdersUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.query = ProcurementOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[PurchaseOrderOverview]:
        self.require_role.execute(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        return self.query.purchase_orders(organization_id)


class ListReorderRecommendationsUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleUsecase(db)
        self.query = ProcurementOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[ReorderRecommendation]:
        self.require_role.execute(
            organization_id=organization_id,
            account_id=account_id,
            allowed_roles={MemberRole.ADMIN.value, MemberRole.WAREHOUSE.value},
        )
        recommendations: list[ReorderRecommendation] = []
        for snapshot in self.query.reorder_policy_snapshots(organization_id):
            decision = reorder_decision(
                on_hand_quantity=snapshot.available_quantity,
                reserved_quantity=0,
                reorder_point=snapshot.reorder_point,
                target_stock_quantity=snapshot.target_stock_quantity,
            )
            if not decision.should_reorder:
                continue
            recommendations.append(
                ReorderRecommendation(
                    policy_id=snapshot.policy_id,
                    warehouse_id=snapshot.warehouse_id,
                    warehouse_name=snapshot.warehouse_name,
                    product_id=snapshot.product_id,
                    sku=snapshot.sku,
                    product_name=snapshot.product_name,
                    supplier_organization_id=snapshot.supplier_organization_id,
                    supplier_name=snapshot.supplier_name,
                    available_quantity=decision.available_quantity,
                    reorder_point=snapshot.reorder_point,
                    target_stock_quantity=snapshot.target_stock_quantity,
                    recommended_quantity=decision.recommended_quantity,
                )
            )
        return recommendations
