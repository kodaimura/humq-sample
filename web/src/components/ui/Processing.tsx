import styles from "@styles/ui/processing.module.css";

type ProcessingProps = {
  text?: string;
};

const Processing = ({ text = "処理中..." }: ProcessingProps) => {
  return (
    <div
      aria-live="assertive"
      className={styles.overlay}
      role="status"
      aria-label={text}
    >
      <div className={styles.bars} aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <p className={styles.text}>{text}</p>
    </div>
  );
};

export default Processing;
