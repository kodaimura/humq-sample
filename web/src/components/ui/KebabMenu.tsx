import { useEffect, useRef, useState, type ReactNode } from "react";
import { EllipsisVertical } from "lucide-react";
import styles from "@styles/ui/kebab-menu.module.css";

type KebabMenuItem = {
  danger?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  label: string;
  onClick: () => void;
};

type KebabMenuProps = {
  ariaLabel?: string;
  disabled?: boolean;
  icon?: ReactNode;
  items: KebabMenuItem[];
};

const KebabMenu = ({
  ariaLabel = "メニューを開く",
  disabled = false,
  icon,
  items,
}: KebabMenuProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div className={styles.wrapper} ref={ref}>
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={ariaLabel}
        className={styles.trigger}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        {icon ?? <EllipsisVertical size={18} />}
      </button>

      {open && (
        <div className={styles.menu} role="menu">
          {items.map((item) => (
            <button
              className={[styles.item, item.danger ? styles.danger : ""]
                .filter(Boolean)
                .join(" ")}
              disabled={item.disabled}
              key={item.label}
              onClick={() => {
                setOpen(false);
                item.onClick();
              }}
              role="menuitem"
              type="button"
            >
              {item.icon && (
                <span className={styles.itemIcon}>{item.icon}</span>
              )}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default KebabMenu;
