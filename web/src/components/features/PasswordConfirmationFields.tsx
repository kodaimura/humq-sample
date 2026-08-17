import type { ChangeEventHandler } from "react";
import { FormField, Help, PasswordInput } from "@ui/index";
import { PASSWORD_MIN_LENGTH } from "@lib/validation";
import styles from "@styles/features/password-confirmation-fields.module.css";

type PasswordConfirmationFieldsProps = {
  autoComplete?: string;
  confirmationId?: string;
  confirmationLabel?: string;
  confirmationName?: string;
  confirmationValue: string;
  onConfirmationChange: ChangeEventHandler<HTMLInputElement>;
  onPasswordChange: ChangeEventHandler<HTMLInputElement>;
  passwordId?: string;
  passwordLabel?: string;
  passwordName?: string;
  passwordValue: string;
};

const PasswordConfirmationFields = ({
  autoComplete,
  confirmationId = "confirm_password",
  confirmationLabel = "パスワード（確認）",
  confirmationName = "confirm_password",
  confirmationValue,
  onConfirmationChange,
  onPasswordChange,
  passwordId = "password",
  passwordLabel = "パスワード",
  passwordName = "password",
  passwordValue,
}: PasswordConfirmationFieldsProps) => (
  <>
    <FormField
      htmlFor={passwordId}
      label={
        <span className={styles.labelWithHelp}>
          {passwordLabel}
          <Help
            align="center"
            text={`${PASSWORD_MIN_LENGTH}文字以上で入力してください。`}
          />
        </span>
      }
      required
    >
      <PasswordInput
        autoComplete={autoComplete}
        id={passwordId}
        minLength={PASSWORD_MIN_LENGTH}
        name={passwordName}
        onChange={onPasswordChange}
        required
        value={passwordValue}
      />
    </FormField>

    <FormField htmlFor={confirmationId} label={confirmationLabel} required>
      <PasswordInput
        autoComplete={autoComplete}
        id={confirmationId}
        minLength={PASSWORD_MIN_LENGTH}
        name={confirmationName}
        onChange={onConfirmationChange}
        required
        value={confirmationValue}
      />
    </FormField>
  </>
);

export default PasswordConfirmationFields;
