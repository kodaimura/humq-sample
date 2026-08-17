import type { ReactNode } from "react";
import { HelpCircle } from "lucide-react";
import Tooltip, { type TooltipAlign } from "./Tooltip";
import styles from "@styles/ui/help.module.css";

type HelpProps = {
  align?: TooltipAlign;
  text: ReactNode;
};

const Help = ({ align, text }: HelpProps) => {
  return (
    <Tooltip align={align} ariaLabel="ヘルプ" content={text}>
      <span className={styles.help} aria-hidden="true">
        <HelpCircle size={16} />
      </span>
    </Tooltip>
  );
};

export default Help;
