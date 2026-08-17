const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const PASSWORD_MIN_LENGTH = 8;

export const validateRequired = (value: string, label: string) => {
  if (!value.trim()) return `${label}を入力してください。`;
  return null;
};

export const validateEmail = (email: string) => {
  const requiredError = validateRequired(email, "メールアドレス");
  if (requiredError) return requiredError;

  if (!EMAIL_PATTERN.test(email)) {
    return "メールアドレスの形式が正しくありません。";
  }

  return null;
};

export const validatePassword = (password: string) => {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `パスワードは${PASSWORD_MIN_LENGTH}文字以上で入力してください。`;
  }

  return null;
};

export const validatePasswordConfirmation = (
  password: string,
  confirmPassword: string,
) => {
  const passwordError = validatePassword(password);
  if (passwordError) return passwordError;

  if (password !== confirmPassword) {
    return "パスワードが一致しません。";
  }

  return null;
};
