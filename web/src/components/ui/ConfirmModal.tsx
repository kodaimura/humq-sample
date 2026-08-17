import Button from "./Button";
import Modal from "./Modal";
import styles from "@styles/ui/confirm-modal.module.css";

type ConfirmVariant = "info" | "warning" | "danger";

type ConfirmModalProps = {
  cancelLabel?: string;
  confirmLabel?: string;
  isOpen: boolean;
  loading?: boolean;
  message?: string;
  onCancel: () => void;
  onConfirm: () => void;
  title?: string;
  variant?: ConfirmVariant;
};

const ConfirmModal = ({
  cancelLabel = "キャンセル",
  confirmLabel = "OK",
  isOpen,
  loading = false,
  message = "この操作を実行しますか？",
  onCancel,
  onConfirm,
  title = "確認",
  variant = "warning",
}: ConfirmModalProps) => {
  const confirmVariant = variant === "danger" ? "danger" : "primary";

  return (
    <Modal
      closeOnOverlayClick={!loading}
      footer={
        <div className={styles.actions}>
          <Button disabled={loading} onClick={onCancel} variant="secondary">
            {cancelLabel}
          </Button>
          <Button
            loading={loading}
            onClick={onConfirm}
            variant={confirmVariant}
          >
            {confirmLabel}
          </Button>
        </div>
      }
      isOpen={isOpen}
      level={variant}
      onClose={onCancel}
      title={title}
    >
      <p className={styles.message}>{message}</p>
    </Modal>
  );
};

export default ConfirmModal;
