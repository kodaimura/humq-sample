import HeaderPrivate from "./HeaderPrivate";
import Footer from "./Footer";
import styles from "@styles/layouts/layout-private.module.css";

type Props = {
  children: React.ReactNode;
};

const LayoutPrivate: React.FC<Props> = ({ children }) => {
  return (
    <div className={styles.container}>
      <HeaderPrivate />
      <main className={styles.main}>{children}</main>
      <Footer />
    </div>
  );
};

export default LayoutPrivate;
