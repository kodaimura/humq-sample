import assert from "node:assert/strict";
import test from "node:test";
import {
  ApiClient,
  accountFixture,
  createAuthenticatedAccount,
  expectStatus,
  login,
  passwords,
} from "./support.mjs";

test("account endpoints provide authenticated CRUD operations", async () => {
  const client = new ApiClient();
  const { accessToken } = await createAuthenticatedAccount(
    client,
    "account-owner",
  );
  const secondary = accountFixture("account-secondary", {
    password: passwords.secondary,
    first_name: "Secondary",
  });
  const created = expectStatus(
    await client.post("/api/accounts", secondary, { token: accessToken }),
    201,
    "create account",
  );
  const secondaryId = created.json?.account?.id;
  assert.equal(typeof secondaryId, "number");
  expectStatus(
    await client.post("/api/accounts", secondary, { token: accessToken }),
    409,
    "reject duplicate account",
  );
  const accounts = expectStatus(
    await client.get("/api/accounts", { token: accessToken }),
    200,
    "list accounts",
  );
  assert.ok(accounts.json?.accounts?.some(({ id }) => id === secondaryId));
  const fetched = expectStatus(
    await client.get(`/api/accounts/${secondaryId}`, { token: accessToken }),
    200,
    "get account",
  );
  assert.equal(fetched.json?.account?.email, secondary.email);
  expectStatus(
    await client.get("/api/accounts/999999999", { token: accessToken }),
    404,
    "missing account",
  );
  const updated = expectStatus(
    await client.put(
      `/api/accounts/${secondaryId}`,
      {
        ...secondary,
        password: passwords.secondaryChanged,
        first_name: "Updated",
      },
      { token: accessToken },
    ),
    200,
    "update account",
  );
  assert.equal(updated.json?.account?.first_name, "Updated");
  const persisted = expectStatus(
    await client.get(`/api/accounts/${secondaryId}`, { token: accessToken }),
    200,
    "get updated account",
  );
  assert.equal(persisted.json?.account?.first_name, "Updated");
  await login(client, secondary.login_id, passwords.secondaryChanged);
});

test("account disable and enable transitions affect authentication", async () => {
  const client = new ApiClient();
  const { accessToken } = await createAuthenticatedAccount(
    client,
    "account-status-owner",
  );
  const secondary = accountFixture("account-status-secondary", {
    password: passwords.secondary,
  });
  const created = expectStatus(
    await client.post("/api/accounts", secondary, { token: accessToken }),
    201,
    "create account for status transition",
  );
  const secondaryId = created.json?.account?.id;
  const disabled = expectStatus(
    await client.put(`/api/accounts/${secondaryId}/disable`, undefined, {
      token: accessToken,
    }),
    200,
    "disable account",
  );
  assert.equal(typeof disabled.json?.account?.disabled_at, "string");
  expectStatus(
    await client.post("/api/auth/login", {
      login_id: secondary.login_id,
      password: secondary.password,
      remember_me: false,
    }),
    401,
    "reject disabled account login",
  );
  const enabled = expectStatus(
    await client.put(`/api/accounts/${secondaryId}/enable`, undefined, {
      token: accessToken,
    }),
    200,
    "enable account",
  );
  assert.equal(enabled.json?.account?.disabled_at, null);
  await login(client, secondary.login_id, secondary.password);
});
