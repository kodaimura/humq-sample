import type { TextareaHTMLAttributes } from "react";
import styles from "@styles/ui/form.module.css";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = ({ className, rows = 4, ...props }: TextareaProps) => {
  const classNames = [styles.control, styles.textarea, className]
    .filter(Boolean)
    .join(" ");

  return <textarea {...props} className={classNames} rows={rows} />;
};

export default Textarea;
