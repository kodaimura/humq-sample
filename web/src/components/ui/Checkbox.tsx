import type { InputHTMLAttributes, ReactNode } from "react";
import styles from "@styles/ui/form.module.css";

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label?: ReactNode;
};

const Checkbox = ({ className, label, ...props }: CheckboxProps) => {
  const inputClassNames = [styles.checkbox, className]
    .filter(Boolean)
    .join(" ");

  if (!label) {
    return <input {...props} className={inputClassNames} type="checkbox" />;
  }

  return (
    <label className={styles.checkboxLabel}>
      <input {...props} className={inputClassNames} type="checkbox" />
      <span>{label}</span>
    </label>
  );
};

export default Checkbox;
