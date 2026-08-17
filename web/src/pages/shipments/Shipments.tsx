import { useCallback, useEffect, useState, type FormEvent } from "react";
import { PackageCheck } from "lucide-react";
import { useOperations } from "@contexts/OperationsContext";
import { api } from "@lib/api";
import type {
  OrdersResponse,
  ShipmentOverview,
  ShipmentsResponse,
  Warehouse,
  WarehousesResponse,
} from "@/features/operations/apiTypes";
import { Button, Input, Select } from "@ui/index";
import { OperationsStatus } from "@components/features/OperationsStatus";
import styles from "@styles/pages/operations/operations.module.css";

const Shipments = () => {
  const { selectedOrganization } = useOperations();
  const organizationId = selectedOrganization?.organization_id;
  const [shipments, setShipments] = useState<ShipmentOverview[]>([]);
  const [orders, setOrders] = useState<OrdersResponse["orders"]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [orderId, setOrderId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [trackingNumbers, setTrackingNumbers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!organizationId) return;
    try {
      const [shipmentResult, orderResult, warehouseResult] = await Promise.all([
        api.get<ShipmentsResponse>(`/organizations/${organizationId}/shipments`),
        api.get<OrdersResponse>(`/organizations/${organizationId}/orders`),
        api.get<WarehousesResponse>(`/organizations/${organizationId}/warehouses`),
      ]);
      setShipments(shipmentResult.shipments);
      setOrders(orderResult.orders);
      setWarehouses(warehouseResult.warehouses);
      setError(null);
    } catch {
      setError("出荷情報を読み込めませんでした。");
    }
  }, [organizationId]);

  useEffect(() => { void load(); }, [load]);

  if (!selectedOrganization) {
    return <div className={styles.page}><p className={styles.empty}>先に組織を作成してください。</p></div>;
  }

  const createShipment = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post(`/orders/${orderId}/shipments`, {
        warehouse_id: Number(warehouseId),
      });
      setOrderId("");
      setWarehouseId("");
      await load();
    } catch {
      setError("出荷を作成できませんでした。選択倉庫に有効な引当があるか確認してください。");
    } finally {
      setSaving(false);
    }
  };

  const ship = async (shipmentId: number) => {
    setSaving(true);
    setError(null);
    try {
      await api.post(`/shipments/${shipmentId}/ship`, {
        tracking_number: trackingNumbers[shipmentId] || null,
      });
      await load();
    } catch {
      setError("出荷確定できませんでした。在庫と引当状態を確認してください。");
    } finally {
      setSaving(false);
    }
  };

  const shippableOrders = orders.filter((order) =>
    ["ALLOCATED", "PARTIALLY_ALLOCATED", "PARTIALLY_SHIPPED"].includes(order.status),
  );

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}><div><p className={styles.eyebrow}>Fulfillment</p><h1 className={styles.title}>出荷管理</h1><p className={styles.description}>引当済み受注を倉庫単位で出荷し、在庫台帳へ反映します。</p></div></header>
      {error && <p className={styles.error}>{error}</p>}
      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>出荷を作成</h2><PackageCheck size={18} /></div>
          <form className={styles.form} onSubmit={createShipment}>
            <div className={styles.field}><label htmlFor="shipment-order">受注</label><Select id="shipment-order" options={shippableOrders.map((order) => ({ label: `${order.order_number} — ${order.customer_name}`, value: String(order.id) }))} placeholder="引当済み受注" required value={orderId} onChange={(event) => setOrderId(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="shipment-warehouse">出荷倉庫</label><Select id="shipment-warehouse" options={warehouses.map((warehouse) => ({ label: warehouse.name, value: String(warehouse.id) }))} placeholder="倉庫を選択" required value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)} /></div>
            <Button disabled={saving || !shippableOrders.length} loading={saving} type="submit">出荷指示を作成</Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>出荷一覧</h2><span className={styles.muted}>{shipments.length} shipments</span></div>
          <div className={styles.tableWrap}><table className={styles.table}><thead><tr><th>出荷番号</th><th>受注</th><th>販売先</th><th>倉庫</th><th>状態</th><th className={styles.number}>数量</th><th>追跡番号</th><th /></tr></thead>
            <tbody>{shipments.map((shipment) => <tr key={shipment.id}><td className={styles.strong}>{shipment.shipment_number}</td><td>{shipment.order_number}</td><td>{shipment.customer_name}</td><td>{shipment.warehouse_name}</td><td><OperationsStatus status={shipment.status} /></td><td className={styles.number}>{shipment.total_quantity}</td><td>{shipment.status === "CONFIRMED" ? <Input aria-label="追跡番号" placeholder="任意" value={trackingNumbers[shipment.id] ?? ""} onChange={(event) => setTrackingNumbers((current) => ({ ...current, [shipment.id]: event.target.value }))} /> : shipment.tracking_number ?? "—"}</td><td>{shipment.status === "CONFIRMED" && <Button disabled={saving} onClick={() => void ship(shipment.id)} size="sm">出荷確定</Button>}</td></tr>)}</tbody>
          </table>{shipments.length === 0 && <p className={styles.empty}>出荷はまだありません。</p>}</div>
        </section>
      </div>
    </div>
  );
};

export default Shipments;
