import { CircleAlert } from "lucide-react";
import styles from "@styles/ui/feedback.module.css";

type MessageVariant = "block" | "inline";

type ErrorMessageProps = {
  className?: string;
  message?: string | null;
  variant?: MessageVariant;
};

const ErrorMessage = ({
  className,
  message,
  variant = "block",
}: ErrorMessageProps) => {
  if (!message) return null;

  const classNames = [styles.message, styles.error, styles[variant], className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classNames} role="alert">
      <CircleAlert aria-hidden="true" className={styles.icon} size={16} />
      <span>{message}</span>
    </div>
  );
};

export default ErrorMessage;
