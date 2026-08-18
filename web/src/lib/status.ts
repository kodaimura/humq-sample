const STATUS_LABELS = {
  ACTIVE: "有効",
  SUSPENDED: "停止中",
  DRAFT: "下書き",
  CONFIRMED: "確定済み",
  PARTIALLY_ALLOCATED: "一部引当",
  ALLOCATED: "引当済み",
  PARTIALLY_SHIPPED: "一部出荷",
  SHIPPED: "出荷済み",
  CANCELED: "取消済み",
  RELEASED: "解放済み",
  CONSUMED: "消化済み",
  APPLIED: "適用済み",
  IN_TRANSIT: "移動中",
  RECEIVED: "入庫済み",
  APPROVED: "承認済み",
  PARTIALLY_RECEIVED: "一部入荷",
  POSTED: "計上済み",
  REQUESTED: "申請済み",
  COMPLETED: "完了",
  ISSUED: "発行済み",
  PARTIALLY_PAID: "一部入金",
  PAID: "入金済み",
  VOID: "無効",
  PENDING: "処理待ち",
  PROCESSED: "処理済み",
  FAILED: "失敗",
} as const;

export const getOperationsStatusLabel = (status: string) =>
  STATUS_LABELS[status as keyof typeof STATUS_LABELS] ??
  status.replaceAll("_", " ");
