import { Link, useNavigate } from "react-router-dom";
import { KeyRound, LogOut, UserCircle } from "lucide-react";
import { useAuth } from "@contexts/AuthContext";
import { KebabMenu } from "@ui/index";
import { ROUTES } from "@/routes";
import styles from "@styles/layouts/header.module.css";

const HeaderPrivate: React.FC = () => {
  const navigate = useNavigate();
  const { account, logout } = useAuth();
  const accountName = account
    ? `${account.last_name} ${account.first_name}`.trim()
    : "Account";

  return (
    <header className={styles.header}>
      <h1 className={styles.logo}>
        <Link to="/">Humq Sample2</Link>
      </h1>
      <nav className={styles.nav}>
        <span className={styles.accountName}>{accountName}</span>
        <KebabMenu
          ariaLabel="アカウントメニューを開く"
          icon={<UserCircle size={20} />}
          items={[
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
