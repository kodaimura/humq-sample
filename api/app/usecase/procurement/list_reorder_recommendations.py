from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.module.business_types import MemberRole
from app.query.procurement_overview import ProcurementOverviewQuery
from app.usecase.organizations._operations import RequireOrganizationRoleOperation
from app.usecase.procurement._policies import reorder_decision


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


class ListReorderRecommendationsUsecase:
    def __init__(self, db: Session):
        self.require_role = RequireOrganizationRoleOperation(db)
        self.query = ProcurementOverviewQuery(db)

    def execute(
        self, *, account_id: int, organization_id: int
    ) -> list[ReorderRecommendation]:
        self.require_role.run(
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
