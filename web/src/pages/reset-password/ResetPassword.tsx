import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "@lib/api";
import { useAuth } from "@contexts/AuthContext";
import { getPasswordResetTokenErrorMessage } from "@lib/errorMessages";
import { waitAtLeast, waitForProcessingPaint } from "@lib/loading";
import { validatePasswordConfirmation } from "@lib/validation";
import type {
  ResetPasswordRequest,
  ResetPasswordVerifyParams,
} from "@/features/auth/apiTypes";
import { ROUTES } from "@/routes";
import PasswordConfirmationFields from "@components/features/PasswordConfirmationFields";
import { Button, ErrorMessage, InfoMessage, Processing } from "@ui/index";
import styles from "@styles/pages/reset-password/reset-password.module.css";

type VerificationState = "checking" | "valid" | "invalid";

const ResetPassword: React.FC = () => {
  const { setAccount, setAccessToken } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [succeeded, setSucceeded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verification, setVerification] =
    useState<VerificationState>("checking");

  useEffect(() => {
    let active = true;

    const verifyToken = async () => {
      if (!token) {
        setError("再設定リンクが正しくありません。");
        setVerification("invalid");
        return;
      }

      try {
        await api.get<void, ResetPasswordVerifyParams>(
          "auth/reset-password/verify",
          { token },
        );
        if (!active) return;
        setVerification("valid");
      } catch (err) {
        if (!active) return;
        setError(getPasswordResetTokenErrorMessage(err));
        setVerification("invalid");
      }
    };

    verifyToken();

    return () => {
      active = false;
    };
  }, [token]);

  const validate = (): string | null => {
    return validatePasswordConfirmation(password, confirmPassword);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    const startedAt = Date.now();
    setLoading(true);
    await waitForProcessingPaint();

    try {
      await api.post<void, ResetPasswordRequest>("auth/reset-password", {
        token,
        new_password: password,
      });
      setAccount(null);
      setAccessToken(null);
      setSucceeded(true);
    } catch (err) {
      setError(getPasswordResetTokenErrorMessage(err));
      setVerification("invalid");
    } finally {
      await waitAtLeast(startedAt);
      setLoading(false);
    }
  };

  const isTokenChecking = verification === "checking";
  const canSubmit = verification === "valid" && !succeeded;

  return (
    <div className={styles.container}>
      {(loading || isTokenChecking) && (
        <Processing text={isTokenChecking ? "確認中..." : "更新中..."} />
      )}
      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        <h1 className={styles.title}>新しいパスワード</h1>
        <p className={styles.description}>
          メールに記載されたリンクから、新しいパスワードを設定します。
        </p>

        <ErrorMessage className={styles.message} message={error} />

        {succeeded && (
          <InfoMessage className={styles.message}>
            パスワードを更新しました。新しいパスワードでログインしてください。
          </InfoMessage>
        )}

        {canSubmit && (
          <>
            <PasswordConfirmationFields
              confirmationLabel="新しいパスワード（確認）"
              confirmationValue={confirmPassword}
              onConfirmationChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              onPasswordChange={(event) => setPassword(event.target.value)}
              passwordLabel="新しいパスワード"
              passwordValue={password}
            />

            <Button
              className={styles.button}
              disabled={loading}
              loading={loading}
              type="submit"
            >
              {loading ? "更新中..." : "パスワードを更新"}
            </Button>
          </>
        )}

        <p className={styles.text}>
          <Link to={ROUTES.login} className={styles.link}>
            ログインへ戻る
          </Link>
        </p>
      </form>
    </div>
  );
};

export default ResetPassword;
