import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import styles from "@styles/ui/modal.module.css";

type ModalLevel = "default" | "info" | "warning" | "danger";

type Props = {
  children?: ReactNode;
  className?: string;
  closeOnOverlayClick?: boolean;
  footer?: ReactNode;
  isOpen: boolean;
  level?: ModalLevel;
  onClose: () => void;
  title?: string;
};

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

const Modal: React.FC<Props> = ({
  children,
  className,
  closeOnOverlayClick = true,
  footer,
  isOpen,
  level = "default",
  onClose,
  title,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  const titleId = useId();

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return;

    const dialog = dialogRef.current;
    const previouslyFocused =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const getFocusableElements = () =>
      dialog
        ? Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
        : [];

    const frameId = window.requestAnimationFrame(() => {
      const [firstFocusable] = getFocusableElements();
      (firstFocusable ?? dialog)?.focus({ preventScroll: true });
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab" || !dialog) return;

      const focusableElements = getFocusableElements();
      const firstFocusable = focusableElements[0];
      const lastFocusable = focusableElements.at(-1);

      if (!firstFocusable || !lastFocusable) {
        event.preventDefault();
        dialog.focus({ preventScroll: true });
        return;
      }

      const activeElement = document.activeElement;
      const focusIsOutside = !dialog.contains(activeElement);

      if (
        event.shiftKey &&
        (activeElement === firstFocusable || focusIsOutside)
      ) {
        event.preventDefault();
        lastFocusable.focus();
      } else if (
        !event.shiftKey &&
        (activeElement === lastFocusable || focusIsOutside)
      ) {
        event.preventDefault();
        firstFocusable.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      window.cancelAnimationFrame(frameId);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = prevOverflow;
      previouslyFocused?.focus({ preventScroll: true });
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!closeOnOverlayClick) return;
    if (e.target === e.currentTarget) onClose();
  };

  const icon =
    level === "danger" ? (
      <AlertCircle size={20} />
    ) : level === "warning" ? (
      <AlertTriangle size={20} />
    ) : level === "info" ? (
      <Info size={20} />
    ) : null;

  return createPortal(
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div
        aria-label={title ? undefined : "ダイアログ"}
        aria-labelledby={title ? titleId : undefined}
        aria-modal="true"
        className={[styles.modal, className].filter(Boolean).join(" ")}
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        <div className={styles.header}>
          <div className={styles.titleRow}>
            {icon && (
              <span
                aria-hidden="true"
                className={[styles.icon, styles[level]].join(" ")}
              >
                {icon}
              </span>
            )}
            {title && (
              <div className={styles.title} id={titleId}>
                {title}
              </div>
            )}
          </div>
          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="閉じる"
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        <div className={styles.body}>{children}</div>

        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body,
  );
};

export default Modal;
