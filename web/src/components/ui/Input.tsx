import { forwardRef, type InputHTMLAttributes } from "react";
import styles from "@styles/ui/form.module.css";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    const classNames = [styles.control, className].filter(Boolean).join(" ");

    return <input {...props} className={classNames} ref={ref} />;
  },
);

Input.displayName = "Input";

export default Input;
