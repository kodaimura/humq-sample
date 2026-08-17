import styles from "@styles/layouts/footer.module.css";

const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <p className={styles.text}>
        Copyright &copy; murakamikodai. {new Date().getFullYear()}.
      </p>
    </footer>
  );
};

export default Footer;
