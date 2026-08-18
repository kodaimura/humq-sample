import { useState, type FormEvent } from "react";
import { Building2, Check } from "lucide-react";
import { api } from "@lib/api";
import { useOperations } from "@contexts/OperationsContext";
import type {
  Organization,
  OrganizationKind,
} from "@/features/operations/apiTypes";
import { Button, Input, Select } from "@ui/index";
import { OperationsStatus } from "@components/features/OperationsStatus";
import styles from "@styles/pages/operations/operations.module.css";

const Organizations = () => {
  const {
    organizations,
    refreshOrganizations,
    selectedOrganization,
    selectOrganization,
  } = useOperations();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [kind, setKind] = useState<OrganizationKind>("CUSTOMER");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const result = await api.post<{ organization: Organization }>(
        "/organizations",
        { code, name, kind, note: note || null },
      );
      await refreshOrganizations();
      selectOrganization(result.organization.id);
      setCode("");
      setName("");
      setNote("");
      setMessage("組織を作成しました。");
    } catch {
      setMessage("組織を作成できませんでした。コードの重複を確認してください。");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <p className={styles.eyebrow}>Organization</p>
          <h1 className={styles.title}>組織管理</h1>
          <p className={styles.description}>
            自社、販売先、仕入先を同じ組織モデルで管理します。
          </p>
        </div>
      </header>

      <div className={styles.grid}>
        <section className={`${styles.card} ${styles.span4}`}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>組織を追加</h2>
            <Building2 size={19} />
          </div>
          <form className={styles.form} onSubmit={submit}>
            <div className={styles.field}>
              <label htmlFor="organization-code">組織コード</label>
              <Input
                id="organization-code"
                onChange={(event) => setCode(event.target.value)}
                placeholder="ACME-JP"
                required
                value={code}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="organization-name">組織名</label>
              <Input
                id="organization-name"
                onChange={(event) => setName(event.target.value)}
                placeholder="アクメ株式会社"
                required
                value={name}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="organization-kind">区分</label>
              <Select
                id="organization-kind"
                onChange={(event) =>
                  setKind(event.target.value as OrganizationKind)
                }
                options={[
                  { label: "販売先", value: "CUSTOMER" },
                  { label: "自社", value: "INTERNAL" },
                  { label: "仕入先", value: "SUPPLIER" },
                ]}
                value={kind}
              />
            </div>
            <div className={styles.field}>
              <label htmlFor="organization-note">備考</label>
              <textarea
                className={styles.textarea}
                id="organization-note"
                onChange={(event) => setNote(event.target.value)}
                value={note}
              />
            </div>
            {message && <p className={styles.muted}>{message}</p>}
            <Button disabled={saving} loading={saving} type="submit">
              組織を作成
            </Button>
          </form>
        </section>

        <section className={`${styles.card} ${styles.span8}`}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>参加組織</h2>
            <span className={styles.muted}>{organizations.length} organizations</span>
          </div>
          {organizations.length === 0 ? (
            <p className={styles.empty}>最初の組織を作成してください。</p>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>コード</th>
                    <th>組織名</th>
                    <th>区分</th>
                    <th>権限</th>
                    <th>状態</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {organizations.map((organization) => {
                    const selected =
                      selectedOrganization?.organization_id ===
                      organization.organization_id;
                    return (
                      <tr key={organization.organization_id}>
                        <td className={styles.strong}>{organization.code}</td>
                        <td>{organization.name}</td>
                        <td>{organization.kind}</td>
                        <td>{organization.role}</td>
                        <td><OperationsStatus status={organization.status} /></td>
                        <td>
                          <Button
                            leftIcon={selected ? <Check size={14} /> : undefined}
                            onClick={() =>
                              selectOrganization(organization.organization_id)
                            }
                            size="sm"
                            variant={selected ? "secondary" : "ghost"}
                          >
                            {selected ? "選択中" : "選択"}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default Organizations;
