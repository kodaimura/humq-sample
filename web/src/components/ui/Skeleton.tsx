import type { CSSProperties } from "react";
import styles from "@styles/ui/feedback.module.css";

type SkeletonProps = {
  className?: string;
  height?: number | string;
  radius?: number | string;
  width?: number | string;
};

const Skeleton = ({
  className,
  height = "1rem",
  radius = 4,
  width = "100%",
}: SkeletonProps) => {
  const style = {
    borderRadius: radius,
    height,
    width,
  } satisfies CSSProperties;

  return (
    <span
      aria-hidden="true"
      className={[styles.skeleton, className].filter(Boolean).join(" ")}
      style={style}
    />
  );
};

export default Skeleton;
