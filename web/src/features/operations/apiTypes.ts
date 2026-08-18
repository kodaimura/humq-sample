export type OrganizationKind = "INTERNAL" | "CUSTOMER" | "SUPPLIER";

export interface OrganizationAccess {
  organization_id: number;
  code: string;
  name: string;
  kind: OrganizationKind;
  status: string;
  role: string;
}

export interface Organization {
  id: number;
  code: string;
  name: string;
  kind: OrganizationKind;
  status: string;
  created_at: string;
}

export interface ProductCategory {
  id: number;
  organization_id: number;
  code: string;
  name: string;
  active: boolean;
}

export interface Product {
  id: number;
  organization_id: number;
  category_id: number | null;
  sku: string;
  name: string;
  description: string | null;
  unit_price: number;
  active: boolean;
  created_at: string;
}

export interface Warehouse {
  id: number;
  organization_id: number;
  code: string;
  name: string;
  active: boolean;
}

export interface InventoryOverview {
  balance_id: number;
  warehouse_id: number;
  warehouse_code: string;
  warehouse_name: string;
  product_id: number;
  sku: string;
  product_name: string;
  on_hand_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface OrderOverview {
  id: number;
  order_number: string;
  customer_name: string;
  status: string;
  requested_ship_date: string | null;
  total_amount: number;
  item_count: number;
  ordered_quantity: number;
  reserved_quantity: number;
  shipped_quantity: number;
  created_at: string;
}

export interface ShipmentOverview {
  id: number;
  shipment_number: string;
  order_id: number;
  order_number: string;
  customer_name: string;
  warehouse_name: string;
  status: string;
  item_count: number;
  total_quantity: number;
  tracking_number: string | null;
  shipped_at: string | null;
  created_at: string;
}

export interface OperationsDashboard {
  open_order_count: number;
  ready_to_ship_count: number;
  shipped_order_count: number;
  total_order_amount: number;
  low_stock_count: number;
}

export interface OrganizationsResponse {
  organizations: OrganizationAccess[];
}

export interface ProductsResponse {
  products: Product[];
}

export interface CategoriesResponse {
  categories: ProductCategory[];
}

export interface WarehousesResponse {
  warehouses: Warehouse[];
}

export interface InventoryResponse {
  inventory: InventoryOverview[];
}

export interface OrdersResponse {
  orders: OrderOverview[];
}

export interface ShipmentsResponse {
  shipments: ShipmentOverview[];
}
