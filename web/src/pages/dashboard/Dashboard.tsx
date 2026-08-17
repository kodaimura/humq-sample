import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Boxes, PackageCheck, ShoppingCart, Warehouse } from "lucide-react";
import { useAuth } from "@contexts/AuthContext";
import { useOperations } from "@contexts/OperationsContext";
import { api } from "@lib/api";
import type { OperationsDashboard } from "@/features/operations/apiTypes";
import { ROUTES } from "@/routes";
import { Button } from "@ui/index";
import { yen } from "@lib/format";
import styles from "@styles/pages/operations/operations.module.css";

const Dashboard = () => {
  const { account } = useAuth();
  const { selectedOrganization } = useOperations();
  const [dashboard, setDashboard] = useState<OperationsDashboard | null>(null);
  const accountName = account ? `${account.last_name} ${account.first_name}`.trim() : "";

  useEffect(() => {
    if (!selectedOrganization) {
      setDashboard(null);
      return;
    }
    void api
      .get<OperationsDashboard>(
        `/organizations/${selectedOrganization.organization_id}/dashboard`,
      )
      .then(setDashboard)
      .catch(() => setDashboard(null));
  }, [selectedOrganization]);

  if (!selectedOrganization) {
    return (
      <div className={styles.page}>
        <section className={styles.card}>
          <p className={styles.eyebrow}>Welcome</p>
          <h1 className={styles.title}>ようこそ、{accountName}さん。</h1>
          <p className={styles.description}>
            最初に自社組織を作成すると、商品・倉庫・受注管理を開始できます。
          </p>
          <div className={styles.actions} style={{ marginTop: "1.5rem" }}>
            <Link to={ROUTES.organizations}>
              <Button rightIcon={<ArrowRight size={16} />}>組織を作成</Button>
            </Link>
          </div>
        </section>
      </div>
    );
  }

  const metrics = [
    ["進行中の受注", dashboard?.open_order_count ?? 0],
    ["出荷準備完了", dashboard?.ready_to_ship_count ?? 0],
    ["出荷済み", dashboard?.shipped_order_count ?? 0],
    ["在庫僅少", dashboard?.low_stock_count ?? 0],
    ["受注総額", yen(dashboard?.total_order_amount ?? 0)],
  ];

  const shortcuts = [
    { icon: <Boxes size={20} />, label: "商品・倉庫", path: ROUTES.catalog },
    { icon: <Warehouse size={20} />, label: "在庫管理", path: ROUTES.inventory },
    { icon: <ShoppingCart size={20} />, label: "受注管理", path: ROUTES.orders },
    { icon: <PackageCheck size={20} />, label: "出荷管理", path: ROUTES.shipments },
  ];

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>Operations Dashboard</p>
          <h1 className={styles.title}>{selectedOrganization.name}</h1>
          <p className={styles.description}>受注・在庫・出荷の現在地をまとめて確認できます。</p>
        </div>
      </header>
      <section className={styles.metricGrid}>
        {metrics.map(([label, value]) => (
          <article className={styles.metric} key={label}>
            <p className={styles.metricLabel}>{label}</p>
            <p className={styles.metricValue}>{value}</p>
          </article>
        ))}
      </section>
      <section className={`${styles.card}`} style={{ marginTop: "1.25rem" }}>
        <div className={styles.cardHeader}><h2 className={styles.cardTitle}>業務メニュー</h2></div>
        <div className={styles.actions}>
          {shortcuts.map((item) => (
            <Link key={item.path} to={item.path}>
              <Button leftIcon={item.icon} variant="secondary">{item.label}</Button>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
