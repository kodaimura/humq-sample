"""Create a coherent B2B demo dataset through the application's Usecases."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import config
from app.core.database import engine
from app.module.account import AccountModule
from app.module.organization import OrganizationModule
from app.module.purchase_order_item import PurchaseOrderItemModule
from app.module.sales_order_item import SalesOrderItemModule
from app.module.sales_return_item import SalesReturnItemModule
from app.usecase.auth.signup import SignupInput, SignupUsecase
from app.usecase.billing.invoices import (
    ChangeInvoiceStatusUsecase,
    GenerateInvoiceInput,
    GenerateInvoiceUsecase,
)
from app.usecase.billing.payments import (
    CreatePaymentInput,
    CreatePaymentUsecase,
    PaymentAllocationInput,
    PostPaymentUsecase,
)
from app.usecase.catalog.categories import CreateCategoryInput, CreateCategoryUsecase
from app.usecase.catalog.products import CreateProductInput, CreateProductUsecase
from app.usecase.catalog.warehouses import CreateWarehouseInput, CreateWarehouseUsecase
from app.usecase.inventory.adjust import (
    AdjustmentLineInput,
    ApplyInventoryAdjustmentInput,
    ApplyInventoryAdjustmentUsecase,
)
from app.usecase.inventory.transfer import (
    CreateTransferInput,
    CreateTransferUsecase,
    ReceiveTransferUsecase,
    ShipTransferUsecase,
    TransferLineInput,
)
from app.usecase.orders.confirm import ConfirmOrderInput, ConfirmOrderUsecase
from app.usecase.orders.create import (
    CreateOrderInput,
    CreateOrderLineInput,
    CreateOrderUsecase,
)
from app.usecase.organizations.add_address import (
    AddOrganizationAddressInput,
    AddOrganizationAddressUsecase,
)
from app.usecase.organizations.create import (
    CreateOrganizationInput,
    CreateOrganizationUsecase,
)
from app.usecase.procurement.catalog import (
    ConfigureReorderPolicyInput,
    ConfigureReorderPolicyUsecase,
    ConfigureSupplierProductInput,
    ConfigureSupplierProductUsecase,
)
from app.usecase.procurement.orders import (
    ChangePurchaseOrderStatusUsecase,
    CreatePurchaseOrderInput,
    CreatePurchaseOrderUsecase,
    PurchaseOrderLineInput,
)
from app.usecase.procurement.receipts import (
    CreateGoodsReceiptInput,
    CreateGoodsReceiptUsecase,
    GoodsReceiptLineInput,
    PostGoodsReceiptUsecase,
)
from app.usecase.returns.receipts import (
    CreateReturnReceiptInput,
    CreateReturnReceiptUsecase,
    PostReturnReceiptUsecase,
    ReturnReceiptLineInput,
)
from app.usecase.returns.requests import (
    ChangeSalesReturnStatusUsecase,
    CreateSalesReturnInput,
    CreateSalesReturnUsecase,
    ReturnLineInput,
)
from app.usecase.shipments.create import CreateShipmentUsecase
from app.usecase.shipments.ship import ShipShipmentUsecase


DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "HumqDemo123!"
DEMO_ORGANIZATION_CODE = "HUMQ-DEMO"


@dataclass(frozen=True)
class DemoContext:
    account_id: int
    seller_id: int
    customer_a_id: int
    customer_b_id: int
    supplier_id: int
    customer_address_id: int
    east_warehouse_id: int
    west_warehouse_id: int
    product_ids: dict[str, int]


@dataclass(frozen=True)
class SeedResult:
    created: bool
    account_id: int
    organization_id: int


def seed_demo() -> SeedResult:
    """Seed once, atomically, while letting each Usecase keep its commit contract."""
    if config.APP_ENV != "dev":
        raise RuntimeError("demo seed is available only when APP_ENV=dev")

    # Usecases commit their own work. A Session joined through savepoints keeps those
    # commits inside this outer transaction, so a later failure rolls back the seed.
    with engine.begin() as connection:
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as db:
            existing_account = AccountModule(db).get_by_email(DEMO_EMAIL)
            existing_organization = OrganizationModule(db).get_by_code(
                DEMO_ORGANIZATION_CODE
            )
            if existing_account and existing_organization:
                return SeedResult(
                    created=False,
                    account_id=existing_account.id,
                    organization_id=existing_organization.id,
                )
            if existing_account or existing_organization:
                raise RuntimeError(
                    "partial demo data already exists; reset the development volume "
                    "with `make down_volumes` before seeding again"
                )

            context = _create_master_data(db)
            _seed_procurement(db, context)
            _seed_inventory_transfer(db, context)
            _seed_order_to_cash(db, context)
            _seed_open_orders(db, context)
            return SeedResult(
                created=True,
                account_id=context.account_id,
                organization_id=context.seller_id,
            )


def _create_master_data(db: Session) -> DemoContext:
    account = SignupUsecase(db).execute(
        SignupInput(
            login_id=DEMO_EMAIL,
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            first_name="Demo",
            last_name="Admin",
        )
    )
    create_organization = CreateOrganizationUsecase(db)
    seller = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code=DEMO_ORGANIZATION_CODE,
            name="HUMQ Manufacturing",
            kind="INTERNAL",
            note="HUMQ architecture demo company",
        )
    )
    customer_a = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-CUST-A",
            name="Aoba Trading",
            kind="CUSTOMER",
            note="Primary demo customer",
        )
    )
    customer_b = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-CUST-B",
            name="Kanto Industrial",
            kind="CUSTOMER",
            note="Customer with open orders",
        )
    )
    supplier = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-SUPP-A",
            name="Shinano Components",
            kind="SUPPLIER",
            note="Preferred demo supplier",
        )
    )

    add_address = AddOrganizationAddressUsecase(db)
    add_address.execute(
        AddOrganizationAddressInput(
            account_id=account.id,
            organization_id=seller.id,
            kind="BILLING",
            name="Head Office",
            postal_code="100-0005",
            prefecture="Tokyo",
            city="Chiyoda-ku",
            address_line1="Marunouchi 1-1-1",
            address_line2=None,
            recipient_name="HUMQ Manufacturing Accounting",
            phone="03-1234-5678",
            is_default=True,
        )
    )
    customer_address = add_address.execute(
        AddOrganizationAddressInput(
            account_id=account.id,
            organization_id=customer_a.id,
            kind="SHIPPING",
            name="Aoba Distribution Center",
            postal_code="231-0001",
            prefecture="Kanagawa",
            city="Yokohama",
            address_line1="Shinko 2-2-1",
            address_line2="Dock 3",
            recipient_name="Aoba Trading Receiving",
            phone="045-123-4567",
            is_default=True,
        )
    )

    create_category = CreateCategoryUsecase(db)
    sensors = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="SENSORS",
            name="Industrial Sensors",
        )
    )
    controllers = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="CONTROLLERS",
            name="Controllers and Gateways",
        )
    )

    create_product = CreateProductUsecase(db)
    product_specs = {
        "temperature": (sensors.id, "TMP-100", "Temperature Sensor", "12000.00"),
        "pressure": (sensors.id, "PRS-200", "Pressure Sensor", "18500.00"),
        "controller": (controllers.id, "CTL-500", "Edge Controller", "42000.00"),
        "gateway": (controllers.id, "GTW-800", "Industrial Gateway", "28000.00"),
    }
    product_ids: dict[str, int] = {}
    for key, (category_id, sku, name, unit_price) in product_specs.items():
        product = create_product.execute(
            CreateProductInput(
                account_id=account.id,
                organization_id=seller.id,
                category_id=category_id,
                sku=sku,
                name=name,
                description=f"Demo catalog item: {name}",
                unit_price=Decimal(unit_price),
            )
        )
        product_ids[key] = product.id

    create_warehouse = CreateWarehouseUsecase(db)
    east = create_warehouse.execute(
        CreateWarehouseInput(
            account_id=account.id,
            organization_id=seller.id,
            code="EAST",
            name="East Distribution Center",
        )
    )
    west = create_warehouse.execute(
        CreateWarehouseInput(
            account_id=account.id,
            organization_id=seller.id,
            code="WEST",
            name="West Distribution Center",
        )
    )

    adjust = ApplyInventoryAdjustmentUsecase(db)
    adjust.execute(
        ApplyInventoryAdjustmentInput(
            account_id=account.id,
            organization_id=seller.id,
            warehouse_id=east.id,
            reason="Demo opening balance",
            items=[
                AdjustmentLineInput(product_ids["temperature"], 30),
                AdjustmentLineInput(product_ids["pressure"], 16),
                AdjustmentLineInput(product_ids["controller"], 10),
                AdjustmentLineInput(product_ids["gateway"], 6),
            ],
        )
    )
    adjust.execute(
        ApplyInventoryAdjustmentInput(
            account_id=account.id,
            organization_id=seller.id,
            warehouse_id=west.id,
            reason="Demo opening balance",
            items=[
                AdjustmentLineInput(product_ids["temperature"], 4),
                AdjustmentLineInput(product_ids["pressure"], 3),
                AdjustmentLineInput(product_ids["controller"], 2),
                AdjustmentLineInput(product_ids["gateway"], 1),
            ],
        )
    )

    return DemoContext(
        account_id=account.id,
        seller_id=seller.id,
        customer_a_id=customer_a.id,
        customer_b_id=customer_b.id,
        supplier_id=supplier.id,
        customer_address_id=customer_address.id,
        east_warehouse_id=east.id,
        west_warehouse_id=west.id,
        product_ids=product_ids,
    )


def _seed_procurement(db: Session, context: DemoContext) -> None:
    supplier_products = ConfigureSupplierProductUsecase(db)
    reorder_policies = ConfigureReorderPolicyUsecase(db)
    procurement_specs = {
        "temperature": ("SUP-TMP-10", "7200.00", 5, 10, 40),
        "pressure": ("SUP-PRS-20", "11000.00", 7, 6, 30),
        "controller": ("SUP-CTL-50", "26000.00", 10, 4, 20),
        "gateway": ("SUP-GTW-80", "17500.00", 12, 5, 18),
    }
    for key, (supplier_sku, unit_cost, lead_time, reorder_point, target) in (
        procurement_specs.items()
    ):
        product_id = context.product_ids[key]
        supplier_products.execute(
            ConfigureSupplierProductInput(
                account_id=context.account_id,
                buyer_organization_id=context.seller_id,
                supplier_organization_id=context.supplier_id,
                product_id=product_id,
                supplier_sku=supplier_sku,
                unit_cost=Decimal(unit_cost),
                lead_time_days=lead_time,
                minimum_order_quantity=2,
            )
        )
        reorder_policies.execute(
            ConfigureReorderPolicyInput(
                account_id=context.account_id,
                organization_id=context.seller_id,
                warehouse_id=context.east_warehouse_id,
                product_id=product_id,
                preferred_supplier_organization_id=context.supplier_id,
                reorder_point=reorder_point,
                target_stock_quantity=target,
            )
        )

    create_order = CreatePurchaseOrderUsecase(db)
    receiving_order = create_order.execute(
        CreatePurchaseOrderInput(
            account_id=context.account_id,
            buyer_organization_id=context.seller_id,
            supplier_organization_id=context.supplier_id,
            warehouse_id=context.east_warehouse_id,
            expected_date=date.today() + timedelta(days=12),
            note="Demo order with a partial receipt",
            items=[
                PurchaseOrderLineInput(context.product_ids["gateway"], 12),
                PurchaseOrderLineInput(context.product_ids["controller"], 6),
            ],
        )
    )
    ChangePurchaseOrderStatusUsecase(db).execute(
        account_id=context.account_id,
        purchase_order_id=receiving_order.id,
        action="approve",
    )
    receiving_items = {
        item.product_id: item
        for item in PurchaseOrderItemModule(db).list_by_order(receiving_order.id)
    }
    receipt = CreateGoodsReceiptUsecase(db).execute(
        CreateGoodsReceiptInput(
            account_id=context.account_id,
            purchase_order_id=receiving_order.id,
            supplier_reference="DEMO-DELIVERY-001",
            note="One gateway was damaged in transit",
            items=[
                GoodsReceiptLineInput(
                    receiving_items[context.product_ids["gateway"]].id,
                    accepted_quantity=5,
                    rejected_quantity=1,
                    rejection_reason="Damaged connector",
                ),
                GoodsReceiptLineInput(
                    receiving_items[context.product_ids["controller"]].id,
                    accepted_quantity=2,
                    rejected_quantity=0,
                ),
            ],
        )
    )
    PostGoodsReceiptUsecase(db).execute(
        account_id=context.account_id,
        goods_receipt_id=receipt.id,
    )
    create_order.execute(
        CreatePurchaseOrderInput(
            account_id=context.account_id,
            buyer_organization_id=context.seller_id,
            supplier_organization_id=context.supplier_id,
            warehouse_id=context.east_warehouse_id,
            expected_date=date.today() + timedelta(days=7),
            note="Demo draft purchase order",
            items=[
                PurchaseOrderLineInput(context.product_ids["temperature"], 20),
            ],
        )
    )


def _seed_inventory_transfer(db: Session, context: DemoContext) -> None:
    transfer = CreateTransferUsecase(db).execute(
        CreateTransferInput(
            account_id=context.account_id,
            organization_id=context.seller_id,
            source_warehouse_id=context.east_warehouse_id,
            destination_warehouse_id=context.west_warehouse_id,
            note="Demo regional stock balancing",
            items=[
                TransferLineInput(context.product_ids["temperature"], 3),
                TransferLineInput(context.product_ids["pressure"], 2),
            ],
        )
    )
    ShipTransferUsecase(db).execute(
        account_id=context.account_id,
        transfer_id=transfer.id,
    )
    ReceiveTransferUsecase(db).execute(
        account_id=context.account_id,
        transfer_id=transfer.id,
    )


def _seed_order_to_cash(db: Session, context: DemoContext) -> None:
    order = CreateOrderUsecase(db).execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_a_id,
            shipping_address_id=context.customer_address_id,
            requested_ship_date=date.today() + timedelta(days=3),
            note="Demo completed fulfillment",
            items=[
                CreateOrderLineInput(context.product_ids["temperature"], 4),
                CreateOrderLineInput(context.product_ids["controller"], 2),
            ],
        )
    )
    ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(account_id=context.account_id, order_id=order.id)
    )
    shipment = CreateShipmentUsecase(db).execute(
        account_id=context.account_id,
        order_id=order.id,
        warehouse_id=context.east_warehouse_id,
        note="Demo outbound shipment",
    )
    ShipShipmentUsecase(db).execute(
        account_id=context.account_id,
        shipment_id=shipment.id,
        tracking_number="HUMQ-DEMO-0001",
    )

    invoice = GenerateInvoiceUsecase(db).execute(
        GenerateInvoiceInput(
            account_id=context.account_id,
            shipment_id=shipment.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
        )
    )
    ChangeInvoiceStatusUsecase(db).execute(
        account_id=context.account_id,
        invoice_id=invoice.id,
        action="issue",
    )
    payment = CreatePaymentUsecase(db).execute(
        CreatePaymentInput(
            account_id=context.account_id,
            payee_organization_id=context.seller_id,
            payer_organization_id=context.customer_a_id,
            payment_date=date.today(),
            amount=Decimal("50000.00"),
            method="BANK_TRANSFER",
            reference="DEMO-BANK-001",
        )
    )
    PostPaymentUsecase(db).execute(
        account_id=context.account_id,
        payment_id=payment.id,
        allocations=[
            PaymentAllocationInput(invoice_id=invoice.id, amount=Decimal("50000.00"))
        ],
    )

    shipped_items = {
        item.product_id: item
        for item in SalesOrderItemModule(db).list_by_order(order.id)
    }
    sales_return = CreateSalesReturnUsecase(db).execute(
        CreateSalesReturnInput(
            account_id=context.account_id,
            order_id=order.id,
            warehouse_id=context.east_warehouse_id,
            reason="CUSTOMER_REQUEST",
            note="Demo return in resalable condition",
            items=[
                ReturnLineInput(
                    shipped_items[context.product_ids["temperature"]].id,
                    quantity=1,
                )
            ],
        )
    )
    ChangeSalesReturnStatusUsecase(db).execute(
        account_id=context.account_id,
        sales_return_id=sales_return.id,
        action="approve",
    )
    return_item = SalesReturnItemModule(db).list_by_return(sales_return.id)[0]
    return_receipt = CreateReturnReceiptUsecase(db).execute(
        CreateReturnReceiptInput(
            account_id=context.account_id,
            sales_return_id=sales_return.id,
            note="Inspected and returned to stock",
            items=[
                ReturnReceiptLineInput(
                    sales_return_item_id=return_item.id,
                    quantity=1,
                    disposition="RESTOCK",
                    condition_note="Factory seal intact",
                )
            ],
        )
    )
    PostReturnReceiptUsecase(db).execute(
        account_id=context.account_id,
        return_receipt_id=return_receipt.id,
    )


def _seed_open_orders(db: Session, context: DemoContext) -> None:
    create_order = CreateOrderUsecase(db)
    create_order.execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_b_id,
            shipping_address_id=None,
            requested_ship_date=date.today() + timedelta(days=10),
            note="Demo draft order awaiting confirmation",
            items=[
                CreateOrderLineInput(context.product_ids["pressure"], 3),
                CreateOrderLineInput(context.product_ids["gateway"], 1),
            ],
        )
    )
    partially_allocated = create_order.execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_b_id,
            shipping_address_id=None,
            requested_ship_date=date.today() + timedelta(days=5),
            note="Demo order exceeding available gateway stock",
            items=[CreateOrderLineInput(context.product_ids["gateway"], 25)],
        )
    )
    ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(
            account_id=context.account_id,
            order_id=partially_allocated.id,
        )
    )
    allocated = create_order.execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_a_id,
            shipping_address_id=context.customer_address_id,
            requested_ship_date=date.today() + timedelta(days=4),
            note="Demo allocated order awaiting shipment",
            items=[CreateOrderLineInput(context.product_ids["pressure"], 3)],
        )
    )
    ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(account_id=context.account_id, order_id=allocated.id)
    )


def main() -> None:
    result = seed_demo()
    state = "created" if result.created else "already present"
    print(f"Demo data {state}.")
    print(f"Login: {DEMO_EMAIL}")
    print(f"Password: {DEMO_PASSWORD}")
    print(f"Organization ID: {result.organization_id}")


if __name__ == "__main__":
    main()
