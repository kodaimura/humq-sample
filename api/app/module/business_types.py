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


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
