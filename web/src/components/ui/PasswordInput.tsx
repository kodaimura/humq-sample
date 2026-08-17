import {
  useLayoutEffect,
  useRef,
  useState,
  type InputHTMLAttributes,
} from "react";
import { Eye, EyeOff } from "lucide-react";
import Input from "./Input";
import styles from "@styles/ui/password-input.module.css";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type">;

type SelectionState = {
  direction: "backward" | "forward" | "none" | null;
  end: number;
  scrollLeft: number;
  start: number;
};

const PasswordInput = ({
  className,
  disabled,
  id,
  ...props
}: PasswordInputProps) => {
  const [visible, setVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const selectionRef = useRef<SelectionState | null>(null);
  const label = visible ? "パスワードを非表示" : "パスワードを表示";

  useLayoutEffect(() => {
    const input = inputRef.current;
    const selection = selectionRef.current;
    if (!input || !selection) return;

    const restoreSelection = () => {
      input.focus({ preventScroll: true });
      input.setSelectionRange(
        Math.min(selection.start, input.value.length),
        Math.min(selection.end, input.value.length),
        selection.direction ?? undefined,
      );
      input.scrollLeft = selection.scrollLeft;
    };

    restoreSelection();
    const timeoutId = window.setTimeout(restoreSelection, 0);
    const frameId = window.requestAnimationFrame(() => {
      restoreSelection();
      selectionRef.current = null;
    });

    return () => {
      window.clearTimeout(timeoutId);
      window.cancelAnimationFrame(frameId);
    };
  }, [visible]);

  const captureSelection = () => {
    const input = inputRef.current;
    if (!input) return;

    selectionRef.current = {
      direction: input.selectionDirection,
      end: input.selectionEnd ?? input.value.length,
      scrollLeft: input.scrollLeft,
      start: input.selectionStart ?? input.value.length,
    };
  };

  const toggleVisibility = () => {
    if (!selectionRef.current) captureSelection();
    setVisible((current) => !current);
  };

  return (
    <div className={styles.wrapper}>
      <Input
        {...props}
        className={[styles.input, className].filter(Boolean).join(" ")}
        disabled={disabled}
        id={id}
        ref={inputRef}
        type={visible ? "text" : "password"}
      />
      <button
        aria-controls={id}
        aria-label={label}
        aria-pressed={visible}
        className={styles.toggle}
        disabled={disabled}
        onClick={toggleVisibility}
        onPointerDown={(event) => {
          captureSelection();
          event.preventDefault();
        }}
        title={label}
        type="button"
      >
        {visible ? (
          <EyeOff aria-hidden="true" size={18} />
        ) : (
          <Eye aria-hidden="true" size={18} />
        )}
      </button>
    </div>
  );
};

export default PasswordInput;
