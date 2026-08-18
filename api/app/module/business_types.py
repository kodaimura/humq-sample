from enum import StrEnum


class OrganizationKind(StrEnum):
    INTERNAL = "INTERNAL"
    CUSTOMER = "CUSTOMER"
    SUPPLIER = "SUPPLIER"


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class MemberRole(StrEnum):
    ADMIN = "ADMIN"
    SALES = "SALES"
    WAREHOUSE = "WAREHOUSE"
    CUSTOMER = "CUSTOMER"


class AddressKind(StrEnum):
    BILLING = "BILLING"
    SHIPPING = "SHIPPING"


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_ALLOCATED = "PARTIALLY_ALLOCATED"
    ALLOCATED = "ALLOCATED"
    PARTIALLY_SHIPPED = "PARTIALLY_SHIPPED"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class ReservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


class ShipmentStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class AdjustmentStatus(StrEnum):
    DRAFT = "DRAFT"
    APPLIED = "APPLIED"
    CANCELED = "CANCELED"


class TransferStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    CANCELED = "CANCELED"


class InventoryEventType(StrEnum):
    ADJUSTMENT = "ADJUSTMENT"
    RESERVATION = "RESERVATION"
    RESERVATION_RELEASED = "RESERVATION_RELEASED"
    SHIPMENT = "SHIPMENT"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    RETURN_RESTOCK = "RETURN_RESTOCK"
    RETURN_DISCARD = "RETURN_DISCARD"


class PurchaseOrderStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELED = "CANCELED"


class GoodsReceiptStatus(StrEnum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELED = "CANCELED"


class SalesReturnStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class ReturnReceiptStatus(StrEnum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELED = "CANCELED"


class ReturnDisposition(StrEnum):
    RESTOCK = "RESTOCK"
    DISCARD = "DISCARD"


class InvoiceStatus(StrEnum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    VOID = "VOID"


class PaymentStatus(StrEnum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELED = "CANCELED"


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
