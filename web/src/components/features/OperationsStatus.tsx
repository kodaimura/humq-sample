import styles from "@styles/pages/operations/operations.module.css";

const toneForStatus = (status: string) => {
  if (["SHIPPED", "ALLOCATED", "APPLIED", "RECEIVED", "ACTIVE"].includes(status))
    return "success";
  if (["PARTIALLY_ALLOCATED", "PARTIALLY_SHIPPED", "IN_TRANSIT"].includes(status))
    return "warning";
  if (["CANCELED", "SUSPENDED", "FAILED"].includes(status)) return "danger";
  return "neutral";
};

export const OperationsStatus = ({ status }: { status: string }) => (
  <span className={styles.badge} data-tone={toneForStatus(status)}>
    {status.replaceAll("_", " ")}
  </span>
);
