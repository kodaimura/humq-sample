import type { ReactNode } from "react";
import { Info } from "lucide-react";
import styles from "@styles/ui/feedback.module.css";

type InfoMessageProps = {
  children: ReactNode;
  className?: string;
};

const InfoMessage = ({ children, className }: InfoMessageProps) => {
  const classNames = [styles.message, styles.info, styles.block, className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classNames} role="status">
      <Info aria-hidden="true" className={styles.icon} size={16} />
      <span>{children}</span>
    </div>
  );
};

export default InfoMessage;
