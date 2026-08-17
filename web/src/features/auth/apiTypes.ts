import type { Account } from "@/types/models";

export type LoginRequest = {
  login_id: string;
  password: string;
};

export type LoginResponse = {
  account: Account;
  access_token: string;
};

export type SignupRequest = {
  email: string;
  first_name: string;
  last_name: string;
  login_id: string;
  password: string;
};

export type ForgotPasswordRequest = {
  email: string;
};

export type ResetPasswordVerifyParams = {
  token: string;
};

export type ResetPasswordRequest = {
  new_password: string;
  token: string;
};
