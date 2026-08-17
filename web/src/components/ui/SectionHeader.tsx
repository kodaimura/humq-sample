import type { ReactNode } from "react";
import styles from "@styles/ui/section-header.module.css";

type SectionHeaderProps = {
  actions?: ReactNode;
  className?: string;
  description?: ReactNode;
  title: ReactNode;
};

const SectionHeader = ({
  actions,
  className,
  description,
  title,
}: SectionHeaderProps) => {
  const classNames = [styles.header, className].filter(Boolean).join(" ");

  return (
    <div className={classNames}>
      <div>
        <h2 className={styles.title}>{title}</h2>
        {description && <p className={styles.description}>{description}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
};

export default SectionHeader;
