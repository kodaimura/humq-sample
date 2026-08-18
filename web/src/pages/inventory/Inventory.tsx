import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ArrowRightLeft, SlidersHorizontal } from "lucide-react";
import { useOperations } from "@contexts/OperationsContext";
import { api } from "@lib/api";
import type {
  InventoryOverview,
  InventoryResponse,
  Product,
  ProductsResponse,
  Warehouse,
  WarehousesResponse,
} from "@/features/operations/apiTypes";
import { Button, Input, Select } from "@ui/index";
import { OperationsStatus } from "@components/features/OperationsStatus";
import styles from "@styles/pages/operations/operations.module.css";

interface Transfer {
  id: number;
  source_warehouse_id: number;
  destination_warehouse_id: number;
  status: string;
}

const Inventory = () => {
  const { selectedOrganization } = useOperations();
  const organizationId = selectedOrganization?.organization_id;
  const [inventory, setInventory] = useState<InventoryOverview[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState("");
  const [productId, setProductId] = useState("");
  const [quantityDelta, setQuantityDelta] = useState("");
  const [reason, setReason] = useState("入荷・棚卸調整");
  const [sourceWarehouseId, setSourceWarehouseId] = useState("");
  const [destinationWarehouseId, setDestinationWarehouseId] = useState("");
  const [transferProductId, setTransferProductId] = useState("");
  const [transferQuantity, setTransferQuantity] = useState("");
  const [latestTransfer, setLatestTransfer] = useState<Transfer | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!organizationId) return;
    try {
      const [inventoryResult, productResult, warehouseResult] =
        await Promise.all([
          api.get<InventoryResponse>(`/organizations/${organizationId}/inventory`),
          api.get<ProductsResponse>(`/organizations/${organizationId}/products`),
          api.get<WarehousesResponse>(`/organizations/${organizationId}/warehouses`),
        ]);
      setInventory(inventoryResult.inventory);
      setProducts(productResult.products);
      setWarehouses(warehouseResult.warehouses);
      setError(null);
    } catch {
      setError("在庫情報を読み込めませんでした。");
    }
  }, [organizationId]);

  useEffect(() => { void load(); }, [load]);

  if (!selectedOrganization) {
    return <div className={styles.page}><p className={styles.empty}>先に組織を作成してください。</p></div>;
  }

  const applyAdjustment = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post(`/organizations/${organizationId}/inventory-adjustments`, {
        warehouse_id: Number(warehouseId),
        reason,
        items: [{ product_id: Number(productId), quantity_delta: Number(quantityDelta) }],
      });
      setQuantityDelta("");
      await load();
    } catch {
      setError("在庫調整を適用できませんでした。引当済み数量を下回っていないか確認してください。");
    } finally {
      setSaving(false);
    }
  };

  const createTransfer = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const result = await api.post<{ transfer: Transfer }>(
        `/organizations/${organizationId}/inventory-transfers`,
        {
          source_warehouse_id: Number(sourceWarehouseId),
          destination_warehouse_id: Number(destinationWarehouseId),
          items: [{ product_id: Number(transferProductId), quantity: Number(transferQuantity) }],
        },
      );
      setLatestTransfer(result.transfer);
    } catch {
      setError("倉庫間移動を作成できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const transitionTransfer = async (action: "ship" | "receive") => {
    if (!latestTransfer) return;
    setSaving(true);
    try {
      const result = await api.post<{ transfer: Transfer }>(
        `/inventory-transfers/${latestTransfer.id}/${action}`,
      );
      setLatestTransfer(result.transfer);
      await load();
    } catch {
      setError("在庫移動の状態を更新できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const warehouseOptions = warehouses.map((item) => ({ label: `${item.code} — ${item.name}`, value: String(item.id) }));
  const productOptions = products.map((item) => ({ label: `${item.sku} — ${item.name}`, value: String(item.id) }));

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div><p className={styles.eyebrow}>Inventory</p><h1 className={styles.title}>在庫管理</h1><p className={styles.description}>実在庫・引当・利用可能数を倉庫別に管理します。</p></div>
      </header>
      {error && <p className={styles.error}>{error}</p>}
      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.span6}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>在庫調整</h2><SlidersHorizontal size={18} /></div>
          <form className={styles.form} onSubmit={applyAdjustment}>
            <div className={styles.formGrid}>
              <div className={styles.field}><label htmlFor="adjust-warehouse">倉庫</label><Select id="adjust-warehouse" options={warehouseOptions} placeholder="倉庫を選択" required value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="adjust-product">商品</label><Select id="adjust-product" options={productOptions} placeholder="商品を選択" required value={productId} onChange={(event) => setProductId(event.target.value)} /></div>
            </div>
            <div className={styles.formGrid}>
              <div className={styles.field}><label htmlFor="adjust-quantity">増減数</label><Input id="adjust-quantity" required type="number" value={quantityDelta} onChange={(event) => setQuantityDelta(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="adjust-reason">理由</label><Input id="adjust-reason" required value={reason} onChange={(event) => setReason(event.target.value)} /></div>
            </div>
            <Button disabled={saving || !products.length || !warehouses.length} type="submit">在庫を調整</Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span6}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>倉庫間移動</h2><ArrowRightLeft size={18} /></div>
          <form className={styles.form} onSubmit={createTransfer}>
            <div className={styles.formGrid}>
              <div className={styles.field}><label htmlFor="transfer-source">移動元</label><Select id="transfer-source" options={warehouseOptions} placeholder="移動元" required value={sourceWarehouseId} onChange={(event) => setSourceWarehouseId(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="transfer-destination">移動先</label><Select id="transfer-destination" options={warehouseOptions} placeholder="移動先" required value={destinationWarehouseId} onChange={(event) => setDestinationWarehouseId(event.target.value)} /></div>
            </div>
            <div className={styles.formGrid}>
              <div className={styles.field}><label htmlFor="transfer-product">商品</label><Select id="transfer-product" options={productOptions} placeholder="商品" required value={transferProductId} onChange={(event) => setTransferProductId(event.target.value)} /></div>
              <div className={styles.field}><label htmlFor="transfer-quantity">数量</label><Input id="transfer-quantity" min="1" required type="number" value={transferQuantity} onChange={(event) => setTransferQuantity(event.target.value)} /></div>
            </div>
            <div className={styles.actions}><Button disabled={saving || warehouses.length < 2} type="submit">移動を作成</Button>
              {latestTransfer?.status === "DRAFT" && <Button onClick={() => void transitionTransfer("ship")} variant="secondary">出庫する</Button>}
              {latestTransfer?.status === "IN_TRANSIT" && <Button onClick={() => void transitionTransfer("receive")} variant="secondary">入庫する</Button>}
              {latestTransfer && <OperationsStatus status={latestTransfer.status} />}
            </div>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span12}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>在庫一覧</h2><span className={styles.muted}>{inventory.length} balances</span></div>
          <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th>倉庫</th><th>SKU</th><th>商品</th><th className={styles.number}>実在庫</th><th className={styles.number}>引当</th><th className={styles.number}>利用可能</th></tr></thead>
            <tbody>{inventory.map((item) => <tr key={item.balance_id}><td>{item.warehouse_name}</td><td className={styles.strong}>{item.sku}</td><td>{item.product_name}</td><td className={styles.number}>{item.on_hand_quantity}</td><td className={styles.number}>{item.reserved_quantity}</td><td className={styles.number}><strong>{item.available_quantity}</strong></td></tr>)}</tbody>
          </table>{inventory.length === 0 && <p className={styles.empty}>在庫調整で初期在庫を登録してください。</p>}</div>
        </section>
      </div>
    </div>
  );
};

export default Inventory;
