import { useAuth } from "@contexts/AuthContext";
import styles from "@styles/pages/dashboard/dashboard.module.css";

const Dashboard: React.FC = () => {
  const { account } = useAuth();
  const accountName = account
    ? `${account.last_name} ${account.first_name}`.trim()
    : null;

  return (
    <div className={styles.container}>
      <section className={styles.welcome}>
        <span className={styles.accent} aria-hidden="true" />
        <p className={styles.label}>Dashboard</p>
        <h1>
          {accountName ? (
            <>
              ようこそ、
              <span>{accountName}</span> さん。
            </>
          ) : (
            "ようこそ。"
          )}
        </h1>
      </section>
    </div>
  );
};

export default Dashboard;
