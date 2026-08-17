import { Link } from "react-router-dom";
import styles from "@styles/layouts/header.module.css";

const HeaderPublic: React.FC = () => {
  return (
    <header className={styles.header}>
      <h1 className={styles.logo}>
        <Link to="/">Humq Sample2</Link>
      </h1>
    </header>
  );
};

export default HeaderPublic;
