import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import {
  ApiClient,
  createAuthenticatedAccount,
  expectStatus,
} from "./support.mjs";

const uniqueCode = (prefix) =>
  `${prefix}-${randomUUID().replaceAll("-", "").slice(0, 10)}`;

test("B2B order fulfillment reserves, ships, and releases inventory", async () => {
  const client = new ApiClient();
  const { accessToken } = await createAuthenticatedAccount(
    client,
    "operations-owner",
  );
  const auth = { token: accessToken };

  const seller = expectStatus(
    await client.post(
      "/api/organizations",
      { code: uniqueCode("seller"), name: "Example Seller", kind: "INTERNAL" },
      auth,
    ),
    201,
    "create seller",
  ).json.organization;
  const customer = expectStatus(
    await client.post(
      "/api/organizations",
      { code: uniqueCode("customer"), name: "Example Customer", kind: "CUSTOMER" },
      auth,
    ),
    201,
    "create customer",
  ).json.organization;

  const category = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/product-categories`,
      { code: uniqueCode("parts"), name: "Parts" },
      auth,
    ),
    201,
    "create category",
  ).json.category;
  const product = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/products`,
      {
        category_id: category.id,
        sku: uniqueCode("sku"),
        name: "Industrial Sensor",
        unit_price: "12000.00",
      },
      auth,
    ),
    201,
    "create product",
  ).json.product;
  const primaryWarehouse = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/warehouses`,
      { code: uniqueCode("east"), name: "East Warehouse" },
      auth,
    ),
    201,
    "create primary warehouse",
  ).json.warehouse;
  const secondaryWarehouse = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/warehouses`,
      { code: uniqueCode("west"), name: "West Warehouse" },
      auth,
    ),
    201,
    "create secondary warehouse",
  ).json.warehouse;

  expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/inventory-adjustments`,
      {
        warehouse_id: primaryWarehouse.id,
        reason: "Opening balance",
        items: [{ product_id: product.id, quantity_delta: 10 }],
      },
      auth,
    ),
    201,
    "apply opening balance",
  );

  const order = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/orders`,
      {
        customer_organization_id: customer.id,
        items: [{ product_id: product.id, quantity: 4 }],
      },
      auth,
    ),
    201,
    "create order",
  ).json.order;
  assert.equal(order.status, "DRAFT");
  assert.equal(order.total_amount, 52800);

  const confirmed = expectStatus(
    await client.post(`/api/orders/${order.id}/confirm`, undefined, auth),
    200,
    "confirm order",
  ).json.order;
  assert.equal(confirmed.status, "ALLOCATED");

  const shipment = expectStatus(
    await client.post(
      `/api/orders/${order.id}/shipments`,
      { warehouse_id: primaryWarehouse.id },
      auth,
    ),
    201,
    "create shipment",
  ).json.shipment;
  const shipped = expectStatus(
    await client.post(
      `/api/shipments/${shipment.id}/ship`,
      { tracking_number: "TRACK-0001" },
      auth,
    ),
    200,
    "ship shipment",
  ).json.shipment;
  assert.equal(shipped.status, "SHIPPED");

  let inventory = expectStatus(
    await client.get(`/api/organizations/${seller.id}/inventory`, auth),
    200,
    "list inventory after shipment",
  ).json.inventory;
  const primaryBalance = inventory.find(
    ({ warehouse_id, product_id }) =>
      warehouse_id === primaryWarehouse.id && product_id === product.id,
  );
  assert.equal(primaryBalance.on_hand_quantity, 6);
  assert.equal(primaryBalance.reserved_quantity, 0);

  const oversizedOrder = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/orders`,
      {
        customer_organization_id: customer.id,
        items: [{ product_id: product.id, quantity: 20 }],
      },
      auth,
    ),
    201,
    "create oversized order",
  ).json.order;
  const partiallyAllocated = expectStatus(
    await client.post(
      `/api/orders/${oversizedOrder.id}/confirm`,
      undefined,
      auth,
    ),
    200,
    "partially allocate order",
  ).json.order;
  assert.equal(partiallyAllocated.status, "PARTIALLY_ALLOCATED");
  expectStatus(
    await client.post(
      `/api/orders/${oversizedOrder.id}/cancel`,
      { reason: "Customer request" },
      auth,
    ),
    200,
    "cancel and release order",
  );

  const transfer = expectStatus(
    await client.post(
      `/api/organizations/${seller.id}/inventory-transfers`,
      {
        source_warehouse_id: primaryWarehouse.id,
        destination_warehouse_id: secondaryWarehouse.id,
        items: [{ product_id: product.id, quantity: 2 }],
      },
      auth,
    ),
    201,
    "create transfer",
  ).json.transfer;
  expectStatus(
    await client.post(`/api/inventory-transfers/${transfer.id}/ship`, undefined, auth),
    200,
    "ship transfer",
  );
  expectStatus(
    await client.post(
      `/api/inventory-transfers/${transfer.id}/receive`,
      undefined,
      auth,
    ),
    200,
    "receive transfer",
  );

  inventory = expectStatus(
    await client.get(`/api/organizations/${seller.id}/inventory`, auth),
    200,
    "list inventory after transfer",
  ).json.inventory;
  assert.equal(
    inventory.find(({ warehouse_id }) => warehouse_id === primaryWarehouse.id)
      .on_hand_quantity,
    4,
  );
  assert.equal(
    inventory.find(({ warehouse_id }) => warehouse_id === secondaryWarehouse.id)
      .on_hand_quantity,
    2,
  );

  const orders = expectStatus(
    await client.get(`/api/organizations/${seller.id}/orders`, auth),
    200,
    "list orders",
  ).json.orders;
  assert.equal(
    orders.find(({ id }) => id === order.id).status,
    "SHIPPED",
  );
  const dashboard = expectStatus(
    await client.get(`/api/organizations/${seller.id}/dashboard`, auth),
    200,
    "operations dashboard",
  ).json;
  assert.equal(dashboard.shipped_order_count, 1);
});
