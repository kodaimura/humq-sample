import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, HttpError } from "@lib/api";
import { getApiErrorMessage } from "@lib/errorMessages";
import { waitAtLeast, waitForProcessingPaint } from "@lib/loading";
import {
  validateEmail,
  validatePasswordConfirmation,
  validateRequired,
} from "@lib/validation";
import type { SignupRequest } from "@/features/auth/apiTypes";
import { ROUTES } from "@/routes";
import PasswordConfirmationFields from "@components/features/PasswordConfirmationFields";
import { Button, ErrorMessage, FormField, Input, Processing } from "@ui/index";
import styles from "@styles/pages/signup/signup.module.css";

const Signup: React.FC = () => {
  const navigate = useNavigate();

  const [lastName, setLastName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validate = (): string | null => {
    return (
      validateRequired(lastName, "姓") ??
      validateRequired(firstName, "名") ??
      validateEmail(email) ??
      validatePasswordConfirmation(password, confirmPassword)
    );
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
      await api.post<void, SignupRequest>("auth/signup", {
        login_id: email,
        first_name: firstName,
        last_name: lastName,
        email,
        password,
      });

      navigate(ROUTES.login);
    } catch (err: unknown) {
      if (err instanceof HttpError && err.status === 409) {
        setError(
          getApiErrorMessage(err, "メールアドレスは既に登録されています。"),
        );
      } else {
        setError("登録に失敗しました。もう一度お試しください。");
      }
    } finally {
      await waitAtLeast(startedAt);
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {loading && <Processing text="登録中..." />}
      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        <h1 className={styles.title}>アカウント登録</h1>

        <ErrorMessage className={styles.message} message={error} />

        <FormField htmlFor="last_name" label="姓" required>
          <Input
            id="last_name"
            type="text"
            name="last_name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
        </FormField>

        <FormField htmlFor="first_name" label="名" required>
          <Input
            id="first_name"
            type="text"
            name="first_name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
        </FormField>

        <FormField htmlFor="email" label="メールアドレス" required>
          <Input
            id="email"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </FormField>

        <PasswordConfirmationFields
          confirmationValue={confirmPassword}
          onConfirmationChange={(event) =>
            setConfirmPassword(event.target.value)
          }
          onPasswordChange={(event) => setPassword(event.target.value)}
          passwordValue={password}
        />

        <Button
          type="submit"
          className={styles.button}
          disabled={loading}
          loading={loading}
        >
          {loading ? "登録中..." : "登録"}
        </Button>

        <p className={styles.text}>
          すでにアカウントをお持ちですか？{" "}
          <Link to={ROUTES.login} className={styles.link}>
            ログイン
          </Link>
        </p>
      </form>
    </div>
  );
};

export default Signup;
