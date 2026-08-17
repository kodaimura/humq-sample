import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Plus, ShoppingCart, Trash2 } from "lucide-react";
import { useOperations } from "@contexts/OperationsContext";
import { api } from "@lib/api";
import type {
  OrderOverview,
  OrdersResponse,
  Product,
  ProductsResponse,
} from "@/features/operations/apiTypes";
import { Button, Input, Select } from "@ui/index";
import { OperationsStatus } from "@components/features/OperationsStatus";
import { yen } from "@lib/format";
import styles from "@styles/pages/operations/operations.module.css";

interface DraftLine {
  product_id: number;
  quantity: number;
}

const Orders = () => {
  const { organizations, selectedOrganization } = useOperations();
  const organizationId = selectedOrganization?.organization_id;
  const [orders, setOrders] = useState<OrderOverview[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [requestedShipDate, setRequestedShipDate] = useState("");
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!organizationId) return;
    try {
      const [orderResult, productResult] = await Promise.all([
        api.get<OrdersResponse>(`/organizations/${organizationId}/orders`),
        api.get<ProductsResponse>(`/organizations/${organizationId}/products`),
      ]);
      setOrders(orderResult.orders);
      setProducts(productResult.products);
      setError(null);
    } catch {
      setError("受注情報を読み込めませんでした。");
    }
  }, [organizationId]);

  useEffect(() => { void load(); }, [load]);

  if (!selectedOrganization) {
    return <div className={styles.page}><p className={styles.empty}>先に組織を作成してください。</p></div>;
  }

  const addLine = () => {
    const id = Number(productId);
    const count = Number(quantity);
    if (!id || count <= 0) return;
    setLines((current) => {
      const existing = current.find((line) => line.product_id === id);
      if (existing) {
        return current.map((line) =>
          line.product_id === id ? { ...line, quantity: line.quantity + count } : line,
        );
      }
      return [...current, { product_id: id, quantity: count }];
    });
    setProductId("");
    setQuantity("1");
  };

  const createOrder = async (event: FormEvent) => {
    event.preventDefault();
    if (!lines.length) {
      setError("商品明細を1件以上追加してください。");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post(`/organizations/${organizationId}/orders`, {
        customer_organization_id: Number(customerId),
        requested_ship_date: requestedShipDate || null,
        items: lines,
      });
      setLines([]);
      setCustomerId("");
      setRequestedShipDate("");
      await load();
    } catch {
      setError("受注を作成できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const transition = async (orderId: number, action: "confirm" | "cancel") => {
    setSaving(true);
    setError(null);
    try {
      await api.post(`/orders/${orderId}/${action}`, action === "cancel" ? { reason: "管理画面からキャンセル" } : undefined);
      await load();
    } catch {
      setError(action === "confirm" ? "在庫引当を実行できませんでした。" : "受注をキャンセルできませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const customers = organizations.filter(
    (organization) => organization.kind === "CUSTOMER",
  );
  const lineTotal = lines.reduce((total, line) => {
    const product = products.find((item) => item.id === line.product_id);
    return total + (product?.unit_price ?? 0) * line.quantity;
  }, 0);

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}><div><p className={styles.eyebrow}>Sales Orders</p><h1 className={styles.title}>受注管理</h1><p className={styles.description}>受注登録から在庫引当、キャンセルまでを管理します。</p></div></header>
      {error && <p className={styles.error}>{error}</p>}
      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.span5}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>新規受注</h2><ShoppingCart size={18} /></div>
          <form className={styles.form} onSubmit={createOrder}>
            <div className={styles.formGrid}>
              <div className={styles.field}><label htmlFor="order-customer">販売先</label><Select id="order-customer" options={customers.map((item) => ({ label: item.name, value: String(item.organization_id) }))} placeholder="販売先を選択" required value={customerId} onChange={(event) => setCustomerId(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="requested-date">出荷希望日</label><Input id="requested-date" type="date" value={requestedShipDate} onChange={(event) => setRequestedShipDate(event.target.value)} /></div>
            </div>
            <div className={styles.lineEditor}>
              <div className={styles.field}><label htmlFor="order-product">商品</label><Select id="order-product" options={products.map((item) => ({ label: `${item.sku} — ${item.name}`, value: String(item.id) }))} placeholder="商品を選択" value={productId} onChange={(event) => setProductId(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="order-quantity">数量</label><Input id="order-quantity" min="1" type="number" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></div>
              <Button disabled={!productId} leftIcon={<Plus size={15} />} onClick={addLine} variant="secondary">追加</Button>
            </div>
            {lines.map((line) => {
              const product = products.find((item) => item.id === line.product_id);
              return <div className={styles.cardHeader} key={line.product_id}><div><p className={styles.strong}>{product?.name}</p><p className={styles.muted}>{line.quantity} × {yen(product?.unit_price ?? 0)}</p></div><Button aria-label="明細を削除" onClick={() => setLines((current) => current.filter((item) => item.product_id !== line.product_id))} size="sm" variant="ghost"><Trash2 size={15} /></Button></div>;
            })}
            {lines.length > 0 && <p className={styles.strong}>小計見込: {yen(lineTotal)}</p>}
            <Button disabled={saving || !customers.length || !lines.length} loading={saving} type="submit">受注を登録</Button>
            {!customers.length && <p className={styles.muted}>組織管理で販売先を追加してください。</p>}
          </form>
        </section>

        <section className={`${styles.card} ${styles.span7}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>受注一覧</h2><span className={styles.muted}>{orders.length} orders</span></div>
          <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th>受注番号</th><th>販売先</th><th>状態</th><th className={styles.number}>数量</th><th className={styles.number}>引当</th><th className={styles.number}>金額</th><th /></tr></thead>
            <tbody>{orders.map((order) => <tr key={order.id}><td className={styles.strong}>{order.order_number}</td><td>{order.customer_name}</td><td><OperationsStatus status={order.status} /></td><td className={styles.number}>{order.ordered_quantity}</td><td className={styles.number}>{order.reserved_quantity}</td><td className={styles.number}>{yen(order.total_amount)}</td><td><div className={styles.actions}>{order.status === "DRAFT" && <Button disabled={saving} onClick={() => void transition(order.id, "confirm")} size="sm">引当</Button>}{["DRAFT", "ALLOCATED", "PARTIALLY_ALLOCATED"].includes(order.status) && <Button disabled={saving} onClick={() => void transition(order.id, "cancel")} size="sm" variant="ghost">取消</Button>}</div></td></tr>)}</tbody>
          </table>{orders.length === 0 && <p className={styles.empty}>受注はまだありません。</p>}</div>
        </section>
      </div>
    </div>
  );
};

export default Orders;
