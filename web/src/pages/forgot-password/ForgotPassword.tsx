import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "@lib/api";
import { waitAtLeast, waitForProcessingPaint } from "@lib/loading";
import { validateEmail } from "@lib/validation";
import type { ForgotPasswordRequest } from "@/features/auth/apiTypes";
import { ROUTES } from "@/routes";
import {
  Button,
  ErrorMessage,
  FormField,
  InfoMessage,
  Input,
  Processing,
} from "@ui/index";
import styles from "@styles/pages/forgot-password/forgot-password.module.css";

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const validate = (): string | null => {
    return validateEmail(email);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSent(false);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    const startedAt = Date.now();
    setLoading(true);
    await waitForProcessingPaint();

    try {
      await api.post<void, ForgotPasswordRequest>("auth/forgot-password", {
        email,
      });
      setSent(true);
    } catch {
      setError("メール送信に失敗しました。もう一度お試しください。");
    } finally {
      await waitAtLeast(startedAt);
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {loading && <Processing text="送信中..." />}
      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        <h1 className={styles.title}>パスワード再設定</h1>
        <p className={styles.description}>
          登録済みのメールアドレスへ再設定用リンクを送信します。
        </p>

        <ErrorMessage className={styles.message} message={error} />

        {sent && (
          <InfoMessage className={styles.message}>
            入力されたメールアドレス宛に、再設定用リンクを送信しました。
          </InfoMessage>
        )}

        <FormField htmlFor="email" label="メールアドレス" required>
          <Input
            id="email"
            name="email"
            onChange={(e) => setEmail(e.target.value)}
            required
            type="email"
            value={email}
          />
        </FormField>

        <Button
          className={styles.button}
          disabled={loading}
          loading={loading}
          type="submit"
        >
          {loading ? "送信中..." : "再設定メールを送信"}
        </Button>

        <p className={styles.text}>
          <Link to={ROUTES.login} className={styles.link}>
            ログインへ戻る
          </Link>
        </p>
      </form>
    </div>
  );
};

export default ForgotPassword;
