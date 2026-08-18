import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Boxes, PackagePlus, Warehouse as WarehouseIcon } from "lucide-react";
import { useOperations } from "@contexts/OperationsContext";
import { api } from "@lib/api";
import type {
  CategoriesResponse,
  Product,
  ProductCategory,
  ProductsResponse,
  Warehouse,
  WarehousesResponse,
} from "@/features/operations/apiTypes";
import { Button, Input, Select } from "@ui/index";
import { yen } from "@lib/format";
import styles from "@styles/pages/operations/operations.module.css";

const Catalog = () => {
  const { selectedOrganization } = useOperations();
  const organizationId = selectedOrganization?.organization_id;
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [categoryCode, setCategoryCode] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [sku, setSku] = useState("");
  const [productName, setProductName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [unitPrice, setUnitPrice] = useState("");
  const [warehouseCode, setWarehouseCode] = useState("");
  const [warehouseName, setWarehouseName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!organizationId) return;
    try {
      const [categoryResult, productResult, warehouseResult] =
        await Promise.all([
          api.get<CategoriesResponse>(
            `/organizations/${organizationId}/product-categories`,
          ),
          api.get<ProductsResponse>(`/organizations/${organizationId}/products`),
          api.get<WarehousesResponse>(
            `/organizations/${organizationId}/warehouses`,
          ),
        ]);
      setCategories(categoryResult.categories);
      setProducts(productResult.products);
      setWarehouses(warehouseResult.warehouses);
      setError(null);
    } catch {
      setError("マスターデータを読み込めませんでした。");
    }
  }, [organizationId]);

  useEffect(() => {
    void load();
  }, [load]);

  const withSaving = async (operation: () => Promise<void>) => {
    setSaving(true);
    setError(null);
    try {
      await operation();
      await load();
    } catch {
      setError("保存できませんでした。入力値やコードの重複を確認してください。");
    } finally {
      setSaving(false);
    }
  };

  if (!selectedOrganization) {
    return <div className={styles.page}><p className={styles.empty}>先に組織を作成してください。</p></div>;
  }

  const createCategory = (event: FormEvent) => {
    event.preventDefault();
    void withSaving(async () => {
      await api.post(`/organizations/${organizationId}/product-categories`, {
        code: categoryCode,
        name: categoryName,
      });
      setCategoryCode("");
      setCategoryName("");
    });
  };

  const createProduct = (event: FormEvent) => {
    event.preventDefault();
    void withSaving(async () => {
      await api.post(`/organizations/${organizationId}/products`, {
        category_id: categoryId ? Number(categoryId) : null,
        sku,
        name: productName,
        unit_price: Number(unitPrice),
      });
      setSku("");
      setProductName("");
      setUnitPrice("");
    });
  };

  const createWarehouse = (event: FormEvent) => {
    event.preventDefault();
    void withSaving(async () => {
      await api.post(`/organizations/${organizationId}/warehouses`, {
        code: warehouseCode,
        name: warehouseName,
      });
      setWarehouseCode("");
      setWarehouseName("");
    });
  };

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>Catalog</p>
          <h1 className={styles.title}>商品・倉庫マスター</h1>
          <p className={styles.description}>{selectedOrganization.name} の販売商品と在庫拠点</p>
        </div>
      </header>
      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>カテゴリ追加</h2><Boxes size={18} /></div>
          <form className={styles.form} onSubmit={createCategory}>
            <div className={styles.field}><label htmlFor="category-code">コード</label><Input id="category-code" required value={categoryCode} onChange={(event) => setCategoryCode(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="category-name">名称</label><Input id="category-name" required value={categoryName} onChange={(event) => setCategoryName(event.target.value)} /></div>
            <Button disabled={saving} type="submit">カテゴリを追加</Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>商品追加</h2><PackagePlus size={18} /></div>
          <form className={styles.form} onSubmit={createProduct}>
            <div className={styles.field}><label htmlFor="product-sku">SKU</label><Input id="product-sku" required value={sku} onChange={(event) => setSku(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="product-name">商品名</label><Input id="product-name" required value={productName} onChange={(event) => setProductName(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="product-category">カテゴリ</label><Select id="product-category" placeholder="未分類" options={categories.map((item) => ({ label: item.name, value: String(item.id) }))} value={categoryId} onChange={(event) => setCategoryId(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="unit-price">標準単価</label><Input id="unit-price" min="1" required type="number" value={unitPrice} onChange={(event) => setUnitPrice(event.target.value)} /></div>
            <Button disabled={saving} type="submit">商品を追加</Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>倉庫追加</h2><WarehouseIcon size={18} /></div>
          <form className={styles.form} onSubmit={createWarehouse}>
            <div className={styles.field}><label htmlFor="warehouse-code">倉庫コード</label><Input id="warehouse-code" required value={warehouseCode} onChange={(event) => setWarehouseCode(event.target.value)} /></div>
            <div className={styles.field}><label htmlFor="warehouse-name">倉庫名</label><Input id="warehouse-name" required value={warehouseName} onChange={(event) => setWarehouseName(event.target.value)} /></div>
            <Button disabled={saving} type="submit">倉庫を追加</Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>商品一覧</h2><span className={styles.muted}>{products.length} products</span></div>
          <div className={styles.tableWrap}>
            <table className={styles.table}><thead><tr><th>SKU</th><th>商品名</th><th>カテゴリ</th><th className={styles.number}>標準単価</th></tr></thead>
              <tbody>{products.map((product) => <tr key={product.id}><td className={styles.strong}>{product.sku}</td><td>{product.name}</td><td>{categories.find((item) => item.id === product.category_id)?.name ?? "—"}</td><td className={styles.number}>{yen(product.unit_price)}</td></tr>)}</tbody>
            </table>
            {products.length === 0 && <p className={styles.empty}>商品はまだありません。</p>}
          </div>
        </section>

        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}><h2 className={styles.cardTitle}>倉庫一覧</h2><span className={styles.muted}>{warehouses.length} warehouses</span></div>
          {warehouses.map((warehouse) => <div key={warehouse.id} className={styles.cardHeader}><span className={styles.strong}>{warehouse.code}</span><span>{warehouse.name}</span></div>)}
          {warehouses.length === 0 && <p className={styles.empty}>倉庫はまだありません。</p>}
        </section>
      </div>
    </div>
  );
};

export default Catalog;
