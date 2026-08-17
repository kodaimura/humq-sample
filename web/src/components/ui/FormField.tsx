import type { ReactNode } from "react";
import ErrorMessage from "./ErrorMessage";
import styles from "@styles/ui/form.module.css";

type FormFieldProps = {
  children: ReactNode;
  className?: string;
  error?: string | null;
  help?: ReactNode;
  htmlFor?: string;
  label: ReactNode;
  required?: boolean;
};

const FormField = ({
  children,
  className,
  error,
  help,
  htmlFor,
  label,
  required = false,
}: FormFieldProps) => {
  const classNames = [styles.field, className].filter(Boolean).join(" ");

  return (
    <div className={classNames}>
      <label className={styles.label} htmlFor={htmlFor}>
        <span>{label}</span>
        {required && <span className={styles.required}>*</span>}
      </label>
      {children}
      {help && <div className={styles.help}>{help}</div>}
      <ErrorMessage message={error} variant="inline" />
    </div>
  );
};

export default FormField;
