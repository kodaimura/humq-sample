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
from app.usecase.orders.cancel import CancelOrderUsecase
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
    customer_c_id: int
    supplier_id: int
    supplier_b_id: int
    customer_address_id: int
    customer_c_address_id: int
    east_warehouse_id: int
    west_warehouse_id: int
    inspection_warehouse_id: int
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
            _seed_additional_order_to_cash(db, context)
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
            first_name="太郎",
            last_name="山田",
        )
    )
    create_organization = CreateOrganizationUsecase(db)
    seller = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code=DEMO_ORGANIZATION_CODE,
            name="HUMQ製造株式会社",
            kind="INTERNAL",
            note="HUMQの業務フローを確認するためのデモ自社組織",
        )
    )
    customer_a = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-CUST-A",
            name="青葉商事株式会社",
            kind="CUSTOMER",
            note="関東圏を担当する主要販売先",
        )
    )
    customer_b = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-CUST-B",
            name="関東産業株式会社",
            kind="CUSTOMER",
            note="未出荷受注を持つデモ販売先",
        )
    )
    customer_c = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-CUST-C",
            name="北星設備株式会社",
            kind="CUSTOMER",
            note="請求・入金済み取引を持つデモ販売先",
        )
    )
    supplier = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-SUPP-A",
            name="信濃部品工業株式会社",
            kind="SUPPLIER",
            note="センサー・保守部品の主要仕入先",
        )
    )
    supplier_b = create_organization.execute(
        CreateOrganizationInput(
            account_id=account.id,
            code="DEMO-SUPP-B",
            name="瀬戸内電子株式会社",
            kind="SUPPLIER",
            note="制御機器・ネットワーク機器の主要仕入先",
        )
    )

    add_address = AddOrganizationAddressUsecase(db)
    add_address.execute(
        AddOrganizationAddressInput(
            account_id=account.id,
            organization_id=seller.id,
            kind="BILLING",
            name="本社経理部",
            postal_code="100-0005",
            prefecture="東京都",
            city="千代田区",
            address_line1="丸の内1-1-1",
            address_line2=None,
            recipient_name="HUMQ製造株式会社 経理部",
            phone="03-1234-5678",
            is_default=True,
        )
    )
    customer_address = add_address.execute(
        AddOrganizationAddressInput(
            account_id=account.id,
            organization_id=customer_a.id,
            kind="SHIPPING",
            name="青葉商事 横浜配送センター",
            postal_code="231-0001",
            prefecture="神奈川県",
            city="横浜市中区",
            address_line1="新港2-2-1",
            address_line2="3番荷受口",
            recipient_name="青葉商事株式会社 商品管理部",
            phone="045-123-4567",
            is_default=True,
        )
    )
    customer_c_address = add_address.execute(
        AddOrganizationAddressInput(
            account_id=account.id,
            organization_id=customer_c.id,
            kind="SHIPPING",
            name="北星設備 札幌物流センター",
            postal_code="060-0005",
            prefecture="北海道",
            city="札幌市中央区",
            address_line1="北五条西2-1",
            address_line2=None,
            recipient_name="北星設備株式会社 資材課",
            phone="011-123-4567",
            is_default=True,
        )
    )

    create_category = CreateCategoryUsecase(db)
    sensors = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="SENSORS",
            name="産業用センサー",
        )
    )
    controllers = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="CONTROLLERS",
            name="制御機器",
        )
    )
    network = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="NETWORK",
            name="ネットワーク機器",
        )
    )
    accessories = create_category.execute(
        CreateCategoryInput(
            account_id=account.id,
            organization_id=seller.id,
            code="ACCESSORIES",
            name="周辺機器・保守部品",
        )
    )

    create_product = CreateProductUsecase(db)
    product_specs = {
        "temperature": (sensors.id, "TMP-100", "温度センサー", "12000.00"),
        "pressure": (sensors.id, "PRS-200", "圧力センサー", "18500.00"),
        "humidity": (sensors.id, "HMS-300", "温湿度センサー", "14800.00"),
        "vibration": (sensors.id, "VBS-400", "振動センサー", "32000.00"),
        "controller": (
            controllers.id,
            "CTL-500",
            "エッジコントローラー",
            "42000.00",
        ),
        "plc": (controllers.id, "PLC-600", "コンパクトPLC", "68000.00"),
        "gateway": (network.id, "GTW-800", "産業用IoTゲートウェイ", "28000.00"),
        "switch": (network.id, "SWT-810", "産業用PoEスイッチ", "36000.00"),
        "power": (accessories.id, "PWR-240", "電源ユニット 24V", "9800.00"),
        "cable": (
            accessories.id,
            "CBL-M12-05",
            "M12センサーケーブル 5m",
            "3500.00",
        ),
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
                description=f"デモ用の商品マスタ：{name}",
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
            name="東日本物流センター",
        )
    )
    west = create_warehouse.execute(
        CreateWarehouseInput(
            account_id=account.id,
            organization_id=seller.id,
            code="WEST",
            name="西日本物流センター",
        )
    )
    inspection = create_warehouse.execute(
        CreateWarehouseInput(
            account_id=account.id,
            organization_id=seller.id,
            code="INSPECTION",
            name="本社検品倉庫",
        )
    )

    adjust = ApplyInventoryAdjustmentUsecase(db)
    adjust.execute(
        ApplyInventoryAdjustmentInput(
            account_id=account.id,
            organization_id=seller.id,
            warehouse_id=east.id,
            reason="デモ初期在庫",
            items=[
                AdjustmentLineInput(product_ids["temperature"], 40),
                AdjustmentLineInput(product_ids["pressure"], 25),
                AdjustmentLineInput(product_ids["humidity"], 18),
                AdjustmentLineInput(product_ids["vibration"], 10),
                AdjustmentLineInput(product_ids["controller"], 12),
                AdjustmentLineInput(product_ids["plc"], 9),
                AdjustmentLineInput(product_ids["gateway"], 8),
                AdjustmentLineInput(product_ids["switch"], 10),
                AdjustmentLineInput(product_ids["power"], 20),
                AdjustmentLineInput(product_ids["cable"], 50),
            ],
        )
    )
    adjust.execute(
        ApplyInventoryAdjustmentInput(
            account_id=account.id,
            organization_id=seller.id,
            warehouse_id=west.id,
            reason="デモ初期在庫",
            items=[
                AdjustmentLineInput(product_ids["temperature"], 8),
                AdjustmentLineInput(product_ids["pressure"], 6),
                AdjustmentLineInput(product_ids["humidity"], 5),
                AdjustmentLineInput(product_ids["vibration"], 3),
                AdjustmentLineInput(product_ids["controller"], 4),
                AdjustmentLineInput(product_ids["plc"], 2),
                AdjustmentLineInput(product_ids["gateway"], 2),
                AdjustmentLineInput(product_ids["switch"], 4),
                AdjustmentLineInput(product_ids["power"], 6),
                AdjustmentLineInput(product_ids["cable"], 15),
            ],
        )
    )
    adjust.execute(
        ApplyInventoryAdjustmentInput(
            account_id=account.id,
            organization_id=seller.id,
            warehouse_id=inspection.id,
            reason="デモ初期在庫",
            items=[
                AdjustmentLineInput(product_ids["temperature"], 2),
                AdjustmentLineInput(product_ids["pressure"], 2),
                AdjustmentLineInput(product_ids["humidity"], 2),
                AdjustmentLineInput(product_ids["vibration"], 1),
                AdjustmentLineInput(product_ids["controller"], 1),
                AdjustmentLineInput(product_ids["plc"], 1),
                AdjustmentLineInput(product_ids["gateway"], 1),
                AdjustmentLineInput(product_ids["switch"], 2),
                AdjustmentLineInput(product_ids["power"], 4),
                AdjustmentLineInput(product_ids["cable"], 10),
            ],
        )
    )

    return DemoContext(
        account_id=account.id,
        seller_id=seller.id,
        customer_a_id=customer_a.id,
        customer_b_id=customer_b.id,
        customer_c_id=customer_c.id,
        supplier_id=supplier.id,
        supplier_b_id=supplier_b.id,
        customer_address_id=customer_address.id,
        customer_c_address_id=customer_c_address.id,
        east_warehouse_id=east.id,
        west_warehouse_id=west.id,
        inspection_warehouse_id=inspection.id,
        product_ids=product_ids,
    )


def _seed_procurement(db: Session, context: DemoContext) -> None:
    supplier_products = ConfigureSupplierProductUsecase(db)
    reorder_policies = ConfigureReorderPolicyUsecase(db)
    procurement_specs = {
        "temperature": (context.supplier_id, "SUP-TMP-10", "7200.00", 5, 10, 40),
        "pressure": (context.supplier_id, "SUP-PRS-20", "11000.00", 7, 8, 35),
        "humidity": (context.supplier_id, "SUP-HMS-30", "8800.00", 6, 8, 30),
        "vibration": (context.supplier_id, "SUP-VBS-40", "20500.00", 9, 5, 20),
        "controller": (context.supplier_b_id, "SUP-CTL-50", "26000.00", 10, 6, 24),
        "plc": (context.supplier_b_id, "SUP-PLC-60", "45000.00", 14, 4, 16),
        "gateway": (context.supplier_b_id, "SUP-GTW-80", "17500.00", 12, 6, 24),
        "switch": (context.supplier_b_id, "SUP-SWT-81", "23000.00", 10, 5, 20),
        "power": (context.supplier_id, "SUP-PWR-24", "5800.00", 4, 10, 36),
        "cable": (context.supplier_id, "SUP-CBL-M12", "1800.00", 3, 20, 80),
    }
    for key, (
        supplier_id,
        supplier_sku,
        unit_cost,
        lead_time,
        reorder_point,
        target,
    ) in procurement_specs.items():
        product_id = context.product_ids[key]
        supplier_products.execute(
            ConfigureSupplierProductInput(
                account_id=context.account_id,
                buyer_organization_id=context.seller_id,
                supplier_organization_id=supplier_id,
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
                preferred_supplier_organization_id=supplier_id,
                reorder_point=reorder_point,
                target_stock_quantity=target,
            )
        )

    create_order = CreatePurchaseOrderUsecase(db)
    receiving_order = create_order.execute(
        CreatePurchaseOrderInput(
            account_id=context.account_id,
            buyer_organization_id=context.seller_id,
            supplier_organization_id=context.supplier_b_id,
            warehouse_id=context.east_warehouse_id,
            expected_date=date.today() + timedelta(days=12),
            note="一部分納と検品不合格を確認するデモ発注",
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
            note="ゲートウェイ1台は端子破損のため受入不可",
            items=[
                GoodsReceiptLineInput(
                    receiving_items[context.product_ids["gateway"]].id,
                    accepted_quantity=5,
                    rejected_quantity=1,
                    rejection_reason="接続端子の破損",
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
            note="承認待ちのデモ発注",
            items=[
                PurchaseOrderLineInput(context.product_ids["temperature"], 20),
                PurchaseOrderLineInput(context.product_ids["humidity"], 12),
                PurchaseOrderLineInput(context.product_ids["cable"], 30),
            ],
        )
    )

    completed_order = create_order.execute(
        CreatePurchaseOrderInput(
            account_id=context.account_id,
            buyer_organization_id=context.seller_id,
            supplier_organization_id=context.supplier_id,
            warehouse_id=context.east_warehouse_id,
            expected_date=date.today(),
            note="全量入荷済みのデモ発注",
            items=[
                PurchaseOrderLineInput(context.product_ids["pressure"], 10),
                PurchaseOrderLineInput(context.product_ids["vibration"], 6),
            ],
        )
    )
    ChangePurchaseOrderStatusUsecase(db).execute(
        account_id=context.account_id,
        purchase_order_id=completed_order.id,
        action="approve",
    )
    completed_items = {
        item.product_id: item
        for item in PurchaseOrderItemModule(db).list_by_order(completed_order.id)
    }
    completed_receipt = CreateGoodsReceiptUsecase(db).execute(
        CreateGoodsReceiptInput(
            account_id=context.account_id,
            purchase_order_id=completed_order.id,
            supplier_reference="DEMO-DELIVERY-002",
            note="予定数量を全量受入",
            items=[
                GoodsReceiptLineInput(
                    completed_items[context.product_ids["pressure"]].id,
                    accepted_quantity=10,
                    rejected_quantity=0,
                ),
                GoodsReceiptLineInput(
                    completed_items[context.product_ids["vibration"]].id,
                    accepted_quantity=6,
                    rejected_quantity=0,
                ),
            ],
        )
    )
    PostGoodsReceiptUsecase(db).execute(
        account_id=context.account_id,
        goods_receipt_id=completed_receipt.id,
    )


def _seed_inventory_transfer(db: Session, context: DemoContext) -> None:
    transfer = CreateTransferUsecase(db).execute(
        CreateTransferInput(
            account_id=context.account_id,
            organization_id=context.seller_id,
            source_warehouse_id=context.east_warehouse_id,
            destination_warehouse_id=context.west_warehouse_id,
            note="東西拠点間の在庫補充",
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
    in_transit = CreateTransferUsecase(db).execute(
        CreateTransferInput(
            account_id=context.account_id,
            organization_id=context.seller_id,
            source_warehouse_id=context.east_warehouse_id,
            destination_warehouse_id=context.inspection_warehouse_id,
            note="本社検品倉庫へ輸送中のデモ移動",
            items=[
                TransferLineInput(context.product_ids["switch"], 2),
                TransferLineInput(context.product_ids["cable"], 5),
            ],
        )
    )
    ShipTransferUsecase(db).execute(
        account_id=context.account_id,
        transfer_id=in_transit.id,
    )


def _seed_order_to_cash(db: Session, context: DemoContext) -> None:
    order = CreateOrderUsecase(db).execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_a_id,
            shipping_address_id=context.customer_address_id,
            requested_ship_date=date.today() + timedelta(days=3),
            note="出荷・請求・一部入金まで完了したデモ受注",
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
        note="青葉商事向け出荷",
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
            note="未使用品1点の返品依頼",
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
            note="検品済みのため良品在庫へ戻す",
            items=[
                ReturnReceiptLineInput(
                    sales_return_item_id=return_item.id,
                    quantity=1,
                    disposition="RESTOCK",
                    condition_note="未開封・外装に損傷なし",
                )
            ],
        )
    )
    PostReturnReceiptUsecase(db).execute(
        account_id=context.account_id,
        return_receipt_id=return_receipt.id,
    )


def _seed_additional_order_to_cash(db: Session, context: DemoContext) -> None:
    order = CreateOrderUsecase(db).execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_c_id,
            shipping_address_id=context.customer_c_address_id,
            requested_ship_date=date.today() + timedelta(days=2),
            note="請求・全額入金済みのデモ受注",
            items=[
                CreateOrderLineInput(context.product_ids["humidity"], 3),
                CreateOrderLineInput(context.product_ids["gateway"], 1),
                CreateOrderLineInput(context.product_ids["power"], 2),
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
        note="北星設備向け出荷",
    )
    ShipShipmentUsecase(db).execute(
        account_id=context.account_id,
        shipment_id=shipment.id,
        tracking_number="HUMQ-DEMO-0002",
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
            payer_organization_id=context.customer_c_id,
            payment_date=date.today(),
            amount=invoice.total_amount,
            method="BANK_TRANSFER",
            reference="DEMO-BANK-002",
        )
    )
    PostPaymentUsecase(db).execute(
        account_id=context.account_id,
        payment_id=payment.id,
        allocations=[
            PaymentAllocationInput(
                invoice_id=invoice.id,
                amount=invoice.total_amount,
            )
        ],
    )

    shipped_item = next(
        item
        for item in SalesOrderItemModule(db).list_by_order(order.id)
        if item.product_id == context.product_ids["humidity"]
    )
    CreateSalesReturnUsecase(db).execute(
        CreateSalesReturnInput(
            account_id=context.account_id,
            order_id=order.id,
            warehouse_id=context.east_warehouse_id,
            reason="QUALITY_ISSUE",
            note="返品承認待ちのデモデータ",
            items=[ReturnLineInput(shipped_item.id, quantity=1)],
        )
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
            note="営業確認待ちの下書き受注",
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
            note="在庫不足により一部引当となるデモ受注",
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
            note="引当済み・出荷作業待ちのデモ受注",
            items=[CreateOrderLineInput(context.product_ids["pressure"], 3)],
        )
    )
    ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(account_id=context.account_id, order_id=allocated.id)
    )

    canceled = create_order.execute(
        CreateOrderInput(
            account_id=context.account_id,
            seller_organization_id=context.seller_id,
            customer_organization_id=context.customer_b_id,
            shipping_address_id=None,
            requested_ship_date=date.today() + timedelta(days=8),
            note="引当後に顧客都合で取消となるデモ受注",
            items=[CreateOrderLineInput(context.product_ids["vibration"], 2)],
        )
    )
    ConfirmOrderUsecase(db).execute(
        ConfirmOrderInput(account_id=context.account_id, order_id=canceled.id)
    )
    CancelOrderUsecase(db).execute(
        account_id=context.account_id,
        order_id=canceled.id,
        reason="顧客の設備計画延期による取消",
    )


def main() -> None:
    result = seed_demo()
    state = "作成しました" if result.created else "投入済みです"
    print(f"デモデータを{state}。")
    print(f"ログインID: {DEMO_EMAIL}")
    print(f"パスワード: {DEMO_PASSWORD}")
    print(f"自社組織ID: {result.organization_id}")


if __name__ == "__main__":
    main()
