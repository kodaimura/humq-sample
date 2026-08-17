import type { ReactNode, SelectHTMLAttributes } from "react";
import styles from "@styles/ui/form.module.css";

type SelectOption = {
  disabled?: boolean;
  label: string;
  value: string;
};

type SelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> & {
  children?: ReactNode;
  options?: SelectOption[];
  placeholder?: string;
};

const Select = ({
  children,
  className,
  options,
  placeholder,
  ...props
}: SelectProps) => {
  const classNames = [styles.control, styles.select, className]
    .filter(Boolean)
    .join(" ");

  return (
    <select {...props} className={classNames}>
      {placeholder && <option value="">{placeholder}</option>}
      {options?.map((option) => (
        <option
          disabled={option.disabled}
          key={option.value}
          value={option.value}
        >
          {option.label}
        </option>
      ))}
      {children}
    </select>
  );
};

export default Select;
