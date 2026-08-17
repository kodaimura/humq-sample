import { describe, expect, it } from "vitest";
import { HttpError } from "@lib/api";
import {
  getApiErrorMessage,
  getPasswordResetTokenErrorMessage,
} from "@lib/errorMessages";
import {
  PASSWORD_MIN_LENGTH,
  validateEmail,
  validatePassword,
  validatePasswordConfirmation,
  validateRequired,
} from "@lib/validation";
import {
  buildLoginPathWithFrom,
  getSafeRedirectPath,
  isPrivateRoutePath,
  isPublicRoutePath,
  ROUTES,
} from "@/routes";

describe("authentication validation", () => {
  it("validates required values and email addresses", () => {
    expect(validateRequired("  ", "名前")).toBe("名前を入力してください。");
    expect(validateRequired("value", "名前")).toBeNull();
    expect(validateEmail("")).toBe("メールアドレスを入力してください。");
    expect(validateEmail("invalid")).toBe(
      "メールアドレスの形式が正しくありません。",
    );
    expect(validateEmail("user@example.com")).toBeNull();
  });

  it("validates password length and confirmation", () => {
    expect(PASSWORD_MIN_LENGTH).toBe(8);
    expect(validatePassword("short")).toBe(
      "パスワードは8文字以上で入力してください。",
    );
    expect(validatePassword("Password123!")).toBeNull();
    expect(validatePasswordConfirmation("short", "short")).toBe(
      "パスワードは8文字以上で入力してください。",
    );
    expect(validatePasswordConfirmation("Password123!", "Password456!")).toBe(
      "パスワードが一致しません。",
    );
    expect(
      validatePasswordConfirmation("Password123!", "Password123!"),
    ).toBeNull();
  });
});

describe("application routes", () => {
  it("classifies every public and private route", () => {
    expect(isPublicRoutePath(ROUTES.login)).toBe(true);
    expect(isPublicRoutePath(ROUTES.signup)).toBe(true);
    expect(isPublicRoutePath(ROUTES.forgotPassword)).toBe(true);
    expect(isPublicRoutePath(ROUTES.resetPassword)).toBe(true);
    expect(isPublicRoutePath(ROUTES.dashboard)).toBe(false);
    expect(isPrivateRoutePath(ROUTES.home)).toBe(true);
    expect(isPrivateRoutePath(ROUTES.dashboard)).toBe(true);
    expect(isPrivateRoutePath(ROUTES.changePassword)).toBe(true);
    expect(isPrivateRoutePath(ROUTES.resetPassword)).toBe(false);
  });

  it("builds and accepts safe internal redirects", () => {
    expect(buildLoginPathWithFrom("/change-password?source=menu")).toBe(
      "/login?from=%2Fchange-password%3Fsource%3Dmenu",
    );
    expect(getSafeRedirectPath("/change-password?source=menu#password")).toBe(
      "/change-password?source=menu#password",
    );
  });

  it.each([
    null,
    "",
    "https://example.com",
    "//example.com",
    "\\example.com",
    ROUTES.login,
    ROUTES.signup,
  ])("rejects unsafe or public redirects: %s", (path) => {
    expect(getSafeRedirectPath(path)).toBe(ROUTES.dashboard);
  });
});

describe("API error messages", () => {
  it.each([
    ["CURRENT_PASSWORD_INCORRECT", "現在のパスワードが正しくありません。"],
    ["EMAIL_ALREADY_EXISTS", "メールアドレスは既に登録されています。"],
    ["INVALID_CREDENTIALS", "メールアドレスまたはパスワードが間違っています。"],
    ["LOGIN_ID_ALREADY_EXISTS", "ログインIDは既に登録されています。"],
  ])("maps %s", (code, message) => {
    expect(getApiErrorMessage(new HttpError(400, code, code), "fallback")).toBe(
      message,
    );
  });

  it.each([
    ["TOKEN_ALREADY_USED", "この再設定リンクは既に使用されています。"],
    ["TOKEN_EXPIRED", "再設定リンクの有効期限が切れています。"],
    ["TOKEN_INVALID", "再設定リンクが正しくありません。"],
  ])("maps reset error %s", (code, message) => {
    expect(
      getPasswordResetTokenErrorMessage(new HttpError(400, code, code)),
    ).toBe(message);
  });

  it("uses fallbacks for unknown failures", () => {
    expect(getApiErrorMessage(new Error("network"), "fallback")).toBe(
      "fallback",
    );
    expect(
      getApiErrorMessage(new HttpError(500, "UNKNOWN", "unknown"), "fallback"),
    ).toBe("fallback");
  });
});
