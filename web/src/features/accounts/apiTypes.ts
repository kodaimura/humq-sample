import type { Account } from "@/types/models";

export type GetCurrentAccountResponse = {
  account: Account;
};

export type ChangePasswordRequest = {
  new_password: string;
  old_password: string;
};
