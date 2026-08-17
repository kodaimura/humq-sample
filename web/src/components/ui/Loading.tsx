import { LoaderCircle } from "lucide-react";
import styles from "@styles/ui/feedback.module.css";

type LoadingProps = {
  className?: string;
  label?: string;
};

const Loading = ({ className, label = "読み込み中..." }: LoadingProps) => {
  const classNames = [styles.loading, className].filter(Boolean).join(" ");

  return (
    <div aria-live="polite" className={classNames} role="status">
      <LoaderCircle aria-hidden="true" className={styles.spinner} size={18} />
      <span>{label}</span>
    </div>
  );
};

export default Loading;
