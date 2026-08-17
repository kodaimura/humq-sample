import assert from "node:assert/strict";
import test from "node:test";
import {
  ApiClient,
  accountFixture,
  assertPublicAccount,
  createAuthenticatedAccount,
  expectStatus,
  login,
  passwords,
  signup,
  waitForResetToken,
} from "./support.mjs";

test("registration and login enforce the public authentication contract", async () => {
  const client = new ApiClient();
  const account = accountFixture("registration");
  await signup(client, account);
  expectStatus(
    await client.post("/api/auth/signup", account),
    409,
    "duplicate signup",
  );
  expectStatus(
    await client.post("/api/auth/login", {
      login_id: account.login_id,
      password: "WrongPassword!",
      remember_me: false,
    }),
    401,
    "invalid login",
  );
  const session = await login(client, account.login_id, account.password);
  const current = expectStatus(
    await client.get("/api/accounts/me", {
      token: session.json.access_token,
    }),
    200,
    "current account",
  );
  assertPublicAccount(current.json?.account, account.email);
});

test("password changes revoke old access and password credentials", async () => {
  const client = new ApiClient();
  const { account, accessToken } = await createAuthenticatedAccount(
    client,
    "password-change",
  );
  expectStatus(
    await client.put(
      "/api/accounts/me/password",
      {
        old_password: "WrongPassword!",
        new_password: passwords.changed,
      },
      { token: accessToken },
    ),
    401,
    "reject incorrect current password",
  );
  expectStatus(
    await client.put(
      "/api/accounts/me/password",
      {
        old_password: account.password,
        new_password: passwords.changed,
      },
      { token: accessToken },
    ),
    204,
    "change password",
  );
  expectStatus(
    await client.get("/api/accounts/me", { token: accessToken }),
    401,
    "revoke old access token",
  );
  expectStatus(
    await client.post("/api/auth/login", {
      login_id: account.login_id,
      password: account.password,
      remember_me: false,
    }),
    401,
    "reject old password",
  );
  const session = await login(client, account.login_id, passwords.changed);
  const refreshed = expectStatus(
    await client.post("/api/auth/refresh", undefined, {
      cookie: session.cookie,
    }),
    200,
    "refresh access token",
  );
  assert.equal(typeof refreshed.json?.access_token, "string");
});

test("password reset is non-enumerating, single-use, and revokes credentials", async () => {
  const client = new ApiClient();
  const { account, session } = await createAuthenticatedAccount(
    client,
    "password-reset",
  );
  expectStatus(
    await client.post("/api/auth/forgot-password", {
      email: accountFixture("missing").email,
    }),
    204,
    "hide unknown password reset account",
  );
  expectStatus(
    await client.post("/api/auth/forgot-password", { email: account.email }),
    204,
    "request password reset",
  );
  const resetToken = await waitForResetToken(account.email);
  expectStatus(
    await client.get("/api/auth/reset-password/verify?token=invalid-token"),
    400,
    "reject invalid reset token",
  );
  expectStatus(
    await client.get(
      `/api/auth/reset-password/verify?token=${encodeURIComponent(resetToken)}`,
    ),
    204,
    "verify reset token",
  );
  expectStatus(
    await client.post("/api/auth/reset-password", {
      token: resetToken,
      new_password: passwords.reset,
    }),
    204,
    "reset password",
  );
  expectStatus(
    await client.get(
      `/api/auth/reset-password/verify?token=${encodeURIComponent(resetToken)}`,
    ),
    400,
    "reject used reset token",
  );
  expectStatus(
    await client.post("/api/auth/login", {
      login_id: account.login_id,
      password: account.password,
      remember_me: false,
    }),
    401,
    "reject pre-reset password",
  );
  expectStatus(
    await client.post("/api/auth/refresh", undefined, {
      cookie: session.cookie,
    }),
    401,
    "revoke refresh token after password reset",
  );
  const resetSession = await login(client, account.login_id, passwords.reset);
  const logout = expectStatus(
    await client.post("/api/auth/logout", undefined, {
      cookie: resetSession.cookie,
    }),
    204,
    "logout",
  );
  assert.match(logout.cookie ?? "", /^refresh_token=/);
});

test("refresh and account endpoints reject missing authentication", async () => {
  const client = new ApiClient();
  expectStatus(
    await client.post("/api/auth/refresh"),
    401,
    "refresh without cookie",
  );
  expectStatus(
    await client.get("/api/accounts/me"),
    401,
    "account without access token",
  );
});
