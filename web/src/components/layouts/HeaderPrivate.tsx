import { Link, NavLink, useNavigate } from "react-router-dom";
import { KeyRound, LogOut, UserCircle } from "lucide-react";
import { useAuth } from "@contexts/AuthContext";
import { useOperations } from "@contexts/OperationsContext";
import { KebabMenu } from "@ui/index";
import { ROUTES } from "@/routes";
import styles from "@styles/layouts/header.module.css";

const links = [
  [ROUTES.home, "概要"],
  [ROUTES.catalog, "商品・倉庫"],
  [ROUTES.inventory, "在庫"],
  [ROUTES.orders, "受注"],
  [ROUTES.shipments, "出荷"],
] as const;

const HeaderPrivate: React.FC = () => {
  const navigate = useNavigate();
  const { account, logout } = useAuth();
  const {
    organizations,
    selectedOrganization,
    selectOrganization,
  } = useOperations();
  const accountName = account
    ? `${account.last_name} ${account.first_name}`.trim()
    : "Account";

  return (
    <header className={styles.header}>
      <div className={styles.brandGroup}>
        <h1 className={styles.logo}>
          <Link to="/">HUMQ Flow</Link>
        </h1>
        {organizations.length > 0 && (
          <select
            aria-label="操作対象の組織"
            className={styles.organizationSelect}
            onChange={(event) => selectOrganization(Number(event.target.value))}
            value={selectedOrganization?.organization_id ?? ""}
          >
            {organizations.map((organization) => (
              <option
                key={organization.organization_id}
                value={organization.organization_id}
              >
                {organization.name}
              </option>
            ))}
          </select>
        )}
      </div>
      <nav className={styles.nav}>
        <div className={styles.primaryNav}>
          {links.map(([path, label]) => (
            <NavLink
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.activeLink : ""}`
              }
              end={path === ROUTES.home}
              key={path}
              to={path}
            >
              {label}
            </NavLink>
          ))}
        </div>
        <span className={styles.accountName}>{accountName}</span>
        <KebabMenu
          ariaLabel="アカウントメニューを開く"
          icon={<UserCircle size={20} />}
          items={[
            {
              icon: <UserCircle size={16} />,
              label: "組織管理",
              onClick: () => navigate(ROUTES.organizations),
            },
            {
              icon: <KeyRound size={16} />,
              label: "パスワード変更",
              onClick: () => navigate(ROUTES.changePassword),
            },
            {
              icon: <LogOut size={16} />,
              label: "ログアウト",
              onClick: logout,
            },
          ]}
        />
      </nav>
    </header>
  );
};

export default HeaderPrivate;
