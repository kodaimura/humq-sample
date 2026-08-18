import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { ApiClient, createAuthenticatedAccount, expectStatus } from "./support.mjs";

const code = (prefix) => `${prefix}-${randomUUID().replaceAll("-", "").slice(0, 10)}`;
const today = new Date().toISOString().slice(0, 10);
const dueDate = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);

test("procurement, returns, invoicing, and payments coordinate inventory and finance", async () => {
  const client = new ApiClient();
  const { accessToken } = await createAuthenticatedAccount(client, "server-domain-owner");
  const auth = { token: accessToken };
  const createOrganization = async (kind, name) => expectStatus(
    await client.post("/api/organizations", { code: code(kind.toLowerCase()), name, kind }, auth),
    201,
    `create ${kind}`,
  ).json.organization;

  const seller = await createOrganization("INTERNAL", "Server Domain Seller");
  const customer = await createOrganization("CUSTOMER", "Server Domain Customer");
  const supplier = await createOrganization("SUPPLIER", "Server Domain Supplier");
  const category = expectStatus(await client.post(`/api/organizations/${seller.id}/product-categories`, { code: code("cat"), name: "Components" }, auth), 201, "create category").json.category;
  const product = expectStatus(await client.post(`/api/organizations/${seller.id}/products`, { category_id: category.id, sku: code("sku"), name: "Control Unit", unit_price: "12000.00" }, auth), 201, "create product").json.product;
  const warehouse = expectStatus(await client.post(`/api/organizations/${seller.id}/warehouses`, { code: code("wh"), name: "Central Warehouse" }, auth), 201, "create warehouse").json.warehouse;

  expectStatus(await client.post(`/api/organizations/${seller.id}/supplier-products`, { supplier_organization_id: supplier.id, product_id: product.id, supplier_sku: code("supplier-sku"), unit_cost: "7000.00", lead_time_days: 5, minimum_order_quantity: 2 }, auth), 201, "configure supplier product");
  expectStatus(await client.post(`/api/organizations/${seller.id}/reorder-policies`, { warehouse_id: warehouse.id, product_id: product.id, preferred_supplier_organization_id: supplier.id, reorder_point: 5, target_stock_quantity: 20 }, auth), 201, "configure reorder policy");
  const recommendations = expectStatus(await client.get(`/api/organizations/${seller.id}/reorder-recommendations`, auth), 200, "list reorder recommendations").json.recommendations;
  assert.equal(recommendations[0].recommended_quantity, 20);

  const purchaseOrder = expectStatus(await client.post(`/api/organizations/${seller.id}/purchase-orders`, { supplier_organization_id: supplier.id, warehouse_id: warehouse.id, items: [{ product_id: product.id, quantity: 10 }] }, auth), 201, "create purchase order").json.purchase_order;
  const purchaseOrderDetails = expectStatus(await client.get(`/api/purchase-orders/${purchaseOrder.id}`, auth), 200, "get purchase order").json;
  const purchaseOrderItem = purchaseOrderDetails.items[0];
  expectStatus(await client.post(`/api/purchase-orders/${purchaseOrder.id}/approve`, {}, auth), 200, "approve purchase order");

  const firstGoodsReceipt = expectStatus(await client.post(`/api/purchase-orders/${purchaseOrder.id}/receipts`, { supplier_reference: "DELIVERY-1", items: [{ purchase_order_item_id: purchaseOrderItem.id, accepted_quantity: 6, rejected_quantity: 1, rejection_reason: "Damaged" }] }, auth), 201, "create partial goods receipt").json.goods_receipt;
  expectStatus(await client.post(`/api/goods-receipts/${firstGoodsReceipt.id}/post`, undefined, auth), 200, "post partial goods receipt");
  let updatedPurchaseOrder = expectStatus(await client.get(`/api/purchase-orders/${purchaseOrder.id}`, auth), 200, "get partial purchase order").json;
  assert.equal(updatedPurchaseOrder.purchase_order.status, "PARTIALLY_RECEIVED");
  assert.equal(updatedPurchaseOrder.items[0].received_quantity, 7);

  const finalGoodsReceipt = expectStatus(await client.post(`/api/purchase-orders/${purchaseOrder.id}/receipts`, { supplier_reference: "DELIVERY-2", items: [{ purchase_order_item_id: purchaseOrderItem.id, accepted_quantity: 3, rejected_quantity: 0 }] }, auth), 201, "create final goods receipt").json.goods_receipt;
  expectStatus(await client.post(`/api/goods-receipts/${finalGoodsReceipt.id}/post`, undefined, auth), 200, "post final goods receipt");
  updatedPurchaseOrder = expectStatus(await client.get(`/api/purchase-orders/${purchaseOrder.id}`, auth), 200, "get received purchase order").json;
  assert.equal(updatedPurchaseOrder.purchase_order.status, "RECEIVED");

  const order = expectStatus(await client.post(`/api/organizations/${seller.id}/orders`, { customer_organization_id: customer.id, items: [{ product_id: product.id, quantity: 4 }] }, auth), 201, "create sales order").json.order;
  expectStatus(await client.post(`/api/orders/${order.id}/confirm`, undefined, auth), 200, "confirm sales order");
  const shipment = expectStatus(await client.post(`/api/orders/${order.id}/shipments`, { warehouse_id: warehouse.id }, auth), 201, "create shipment").json.shipment;
  expectStatus(await client.post(`/api/shipments/${shipment.id}/ship`, { tracking_number: "SERVER-DOMAIN-TRACK" }, auth), 200, "ship order");

  const eligibility = expectStatus(await client.get(`/api/orders/${order.id}/return-eligibility`, auth), 200, "get return eligibility").json.items[0];
  assert.equal(eligibility.returnable_quantity, 4);
  const salesReturn = expectStatus(await client.post(`/api/orders/${order.id}/returns`, { warehouse_id: warehouse.id, reason: "CUSTOMER_REQUEST", items: [{ order_item_id: eligibility.order_item_id, quantity: 3 }] }, auth), 201, "request return").json.sales_return;
  const returnDetails = expectStatus(await client.get(`/api/returns/${salesReturn.id}`, auth), 200, "get return details").json;
  const returnItem = returnDetails.items[0];
  expectStatus(await client.post(`/api/returns/${salesReturn.id}/approve`, {}, auth), 200, "approve return");

  const restockReceipt = expectStatus(await client.post(`/api/returns/${salesReturn.id}/receipts`, { items: [{ sales_return_item_id: returnItem.id, quantity: 2, disposition: "RESTOCK" }] }, auth), 201, "create restock receipt").json.return_receipt;
  expectStatus(await client.post(`/api/return-receipts/${restockReceipt.id}/post`, undefined, auth), 200, "post restock receipt");
  const discardReceipt = expectStatus(await client.post(`/api/returns/${salesReturn.id}/receipts`, { items: [{ sales_return_item_id: returnItem.id, quantity: 1, disposition: "DISCARD", condition_note: "Broken housing" }] }, auth), 201, "create discard receipt").json.return_receipt;
  expectStatus(await client.post(`/api/return-receipts/${discardReceipt.id}/post`, undefined, auth), 200, "post discard receipt");
  assert.equal(expectStatus(await client.get(`/api/returns/${salesReturn.id}`, auth), 200, "get completed return").json.sales_return.status, "COMPLETED");

  const inventory = expectStatus(await client.get(`/api/organizations/${seller.id}/inventory`, auth), 200, "get inventory after returns").json.inventory;
  assert.equal(inventory.find((item) => item.product_id === product.id).on_hand_quantity, 7);

  const invoice = expectStatus(await client.post(`/api/shipments/${shipment.id}/invoices`, { issue_date: today, due_date: dueDate }, auth), 201, "generate invoice").json.invoice;
  assert.equal(Number(invoice.total_amount), 52800);
  const issuedInvoice = expectStatus(await client.post(`/api/invoices/${invoice.id}/issue`, {}, auth), 200, "issue invoice").json.invoice;
  assert.equal(issuedInvoice.status, "ISSUED");

  const firstPayment = expectStatus(await client.post(`/api/organizations/${seller.id}/payments`, { payer_organization_id: customer.id, payment_date: today, amount: "30000.00", method: "BANK_TRANSFER", reference: "BANK-1" }, auth), 201, "create first payment").json.payment;
  const postedFirstPayment = expectStatus(await client.post(`/api/payments/${firstPayment.id}/post`, { allocations: [{ invoice_id: invoice.id, amount: "30000.00" }] }, auth), 200, "post first payment").json.payment;
  assert.equal(Number(postedFirstPayment.unallocated_amount), 0);

  const finalPayment = expectStatus(await client.post(`/api/organizations/${seller.id}/payments`, { payer_organization_id: customer.id, payment_date: today, amount: "22800.00", method: "BANK_TRANSFER", reference: "BANK-2" }, auth), 201, "create final payment").json.payment;
  expectStatus(await client.post(`/api/payments/${finalPayment.id}/post`, { allocations: [{ invoice_id: invoice.id, amount: "22800.00" }] }, auth), 200, "post final payment");
  const receivables = expectStatus(await client.get(`/api/organizations/${seller.id}/receivables`, auth), 200, "get receivables").json.receivables;
  assert.equal(Number(receivables[0].balance_due), 0);
});
