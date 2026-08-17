import HeaderPublic from "./HeaderPublic";
import Footer from "./Footer";
import styles from "@styles/layouts/layout-public.module.css";

type Props = {
  children: React.ReactNode;
};

const LayoutPublic: React.FC<Props> = ({ children }) => {
  return (
    <div className={styles.container}>
      <HeaderPublic />
      <main className={styles.main}>{children}</main>
      <Footer />
    </div>
  );
};

export default LayoutPublic;
