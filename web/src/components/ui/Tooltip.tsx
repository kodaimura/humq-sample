import { useId, useRef, useState, type ReactNode } from "react";
import styles from "@styles/ui/tooltip.module.css";

export type TooltipAlign = "left" | "center" | "right";

type TooltipProps = {
  align?: TooltipAlign;
  ariaLabel?: string;
  bubbleClassName?: string;
  children: ReactNode;
  className?: string;
  content: ReactNode;
};

const Tooltip = ({
  align = "left",
  ariaLabel,
  bubbleClassName,
  children,
  className,
  content,
}: TooltipProps) => {
  const id = useId();
  const ref = useRef<HTMLSpanElement>(null);
  const [effectiveAlign, setEffectiveAlign] = useState<TooltipAlign>(align);

  const updateAlignment = () => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const windowWidth = window.innerWidth;

    if (rect.right > windowWidth - 200) {
      setEffectiveAlign("right");
    } else if (rect.left < 200) {
      setEffectiveAlign("left");
    } else {
      setEffectiveAlign(align);
    }
  };

  const wrapperClassName = [
    styles.wrapper,
    styles[`align${effectiveAlign[0].toUpperCase()}${effectiveAlign.slice(1)}`],
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span
      aria-describedby={id}
      aria-label={ariaLabel}
      className={wrapperClassName}
      onFocus={updateAlignment}
      onMouseEnter={updateAlignment}
      ref={ref}
      tabIndex={0}
    >
      {children}
      <span
        className={[styles.bubble, bubbleClassName].filter(Boolean).join(" ")}
        id={id}
        role="tooltip"
      >
        {content}
      </span>
    </span>
  );
};

export default Tooltip;
