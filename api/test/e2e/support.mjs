import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";

const apiOrigin = process.env.API_ORIGIN ?? "http://api:8000";
const mailhogUrl = process.env.MAILHOG_URL ?? "http://mailhog:8025";

export const passwords = {
  initial: "Password123!",
  changed: "Changed123!",
  reset: "Reset123!",
  secondary: "Secondary123!",
  secondaryChanged: "Secondary456!",
};

export class ApiClient {
  constructor(origin = apiOrigin) {
    this.origin = origin.replace(/\/+$/, "");
  }

  async request(path, { method = "GET", body, token, cookie } = {}) {
    const headers = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    if (cookie) headers.Cookie = cookie;

    const response = await fetch(`${this.origin}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let json;
    if (text) {
      try {
        json = JSON.parse(text);
      } catch {
        json = undefined;
      }
    }
    return {
      status: response.status,
      json,
      cookie: response.headers.get("set-cookie")?.split(";", 1)[0],
    };
  }

  get(path, options = {}) {
    return this.request(path, options);
  }

  post(path, body, options = {}) {
    return this.request(path, { ...options, method: "POST", body });
  }

  put(path, body, options = {}) {
    return this.request(path, { ...options, method: "PUT", body });
  }
}

export const expectStatus = (response, status, label) => {
  assert.equal(
    response.status,
    status,
    `${label}: expected ${status}, received ${response.status} ${JSON.stringify(response.json)}`,
  );
  return response;
};

export const assertPublicAccount = (account, expectedEmail) => {
  assert.equal(account?.email, expectedEmail);
  assert.equal(typeof account?.id, "number");
  assert.equal("password" in account, false);
  assert.equal("password_hash" in account, false);
};

export const accountFixture = (label, overrides = {}) => {
  const uniqueId = randomUUID().replaceAll("-", "");
  const email = `${label}-${uniqueId}@example.com`;
  return {
    email,
    login_id: email,
    password: passwords.initial,
    first_name: "Test",
    last_name: "Account",
    ...overrides,
  };
};

export const signup = async (client, account) => {
  const response = expectStatus(
    await client.post("/api/auth/signup", account),
    201,
    "signup",
  );
  assertPublicAccount(response.json?.account, account.email);
  return response;
};

export const login = async (client, loginId, password) => {
  const response = expectStatus(
    await client.post("/api/auth/login", {
      login_id: loginId,
      password,
      remember_me: false,
    }),
    200,
    "login",
  );
  assert.equal(typeof response.json?.access_token, "string");
  assert.ok(response.cookie?.startsWith("refresh_token="));
  return response;
};

export const createAuthenticatedAccount = async (client, label) => {
  const account = accountFixture(label);
  await signup(client, account);
  const session = await login(client, account.login_id, account.password);
  return {
    account,
    accessToken: session.json.access_token,
    session,
  };
};

const decodeQuotedPrintable = (body) =>
  body
    ?.replace(/=\r?\n/g, "")
    .replace(/=([0-9A-F]{2})/gi, (_, hex) =>
      String.fromCharCode(Number.parseInt(hex, 16)),
    );

export const waitForResetToken = async (email) => {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const response = await fetch(`${mailhogUrl}/api/v2/messages?limit=50`);
    assert.equal(response.status, 200);
    const messages = await response.json();
    const message = messages.items?.find((item) =>
      item.To?.some(
        (recipient) => `${recipient.Mailbox}@${recipient.Domain}` === email,
      ),
    );
    if (message) {
      const body = decodeQuotedPrintable(message.Content?.Body);
      const token = body?.match(/[?&]token=([A-Za-z0-9_-]+)/)?.[1];
      assert.ok(token, "password reset token is missing from the email");
      return token;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  assert.fail(`password reset email was not delivered to ${email}`);
};
