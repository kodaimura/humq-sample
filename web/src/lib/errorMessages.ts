import { HttpError } from "@lib/api";

const API_ERROR_MESSAGES: Record<string, string> = {
  CURRENT_PASSWORD_INCORRECT: "現在のパスワードが正しくありません。",
  EMAIL_ALREADY_EXISTS: "メールアドレスは既に登録されています。",
  INVALID_CREDENTIALS: "メールアドレスまたはパスワードが間違っています。",
  LOGIN_ID_ALREADY_EXISTS: "ログインIDは既に登録されています。",
};

const PASSWORD_RESET_TOKEN_ERROR_MESSAGES: Record<string, string> = {
  TOKEN_ALREADY_USED: "この再設定リンクは既に使用されています。",
  TOKEN_EXPIRED: "再設定リンクの有効期限が切れています。",
  TOKEN_INVALID: "再設定リンクが正しくありません。",
};

export const getApiErrorMessage = (err: unknown, fallback: string) => {
  if (!(err instanceof HttpError)) return fallback;

  return API_ERROR_MESSAGES[err.code] ?? fallback;
};

export const getPasswordResetTokenErrorMessage = (
  err: unknown,
  fallback = "再設定リンクを確認できませんでした。",
) => {
  if (!(err instanceof HttpError)) return fallback;

  return PASSWORD_RESET_TOKEN_ERROR_MESSAGES[err.code] ?? fallback;
};
