import { useNavigate } from "react-router-dom";
import styles from "@styles/pages/notfound/notfound.module.css";

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>404</h1>
      <p className={styles.message}>ページが見つかりませんでした。</p>
      <button className={styles.button} onClick={() => navigate("/")}>
        ホームに戻る
      </button>
    </div>
  );
};

export default NotFound;
