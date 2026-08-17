import { beforeEach, describe, expect, it, vi } from "vitest";
import { Api, HttpError } from "@lib/api";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status,
  });

describe("Api", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    window.history.replaceState({}, "", "/login");
  });

  it("builds authenticated GET requests and filters empty query values", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");
    api.setAccessToken("access-token");

    await expect(
      api.get("/accounts", {
        active: false,
        empty: null,
        page: 2,
        query: "hello world",
        unset: undefined,
      }),
    ).resolves.toEqual({ ok: true });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/accounts?active=false&page=2&query=hello+world",
      expect.objectContaining({
        credentials: "include",
        headers: { Authorization: "Bearer access-token" },
        method: "GET",
      }),
    );
  });

  it.each(["post", "put", "patch", "delete"] as const)(
    "sends JSON for %s requests",
    async (method) => {
      const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
      vi.stubGlobal("fetch", fetchMock);
      const api = new Api("http://api.test");

      await api[method]("accounts", { value: 1 });

      expect(fetchMock).toHaveBeenCalledWith(
        "http://api.test/accounts",
        expect.objectContaining({
          body: JSON.stringify({ value: 1 }),
          headers: { "Content-Type": "application/json" },
          method: method.toUpperCase(),
        }),
      );
    },
  );

  it("passes FormData through without setting a JSON content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");
    const form = new FormData();
    form.set("file", "contents");

    await api.post("upload", form);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/upload",
      expect.objectContaining({ body: form, headers: {} }),
    );
  });

  it("returns an empty object for successful responses without content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await expect(
      new Api("http://api.test").post("auth/logout"),
    ).resolves.toEqual({});
  });

  it("normalizes structured and non-JSON HTTP errors", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(
          { code: "INVALID_INPUT", errors: { email: "invalid" } },
          422,
        ),
      )
      .mockResolvedValueOnce(new Response("broken", { status: 500 }));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");

    await expect(api.post("accounts", {})).rejects.toMatchObject({
      code: "INVALID_INPUT",
      details: { email: "invalid" },
      status: 422,
    });
    await expect(api.get("failure")).rejects.toMatchObject({
      code: "UNKNOWN_ERROR",
      message: "Unknown error",
      status: 500,
    });
  });

  it("refreshes once and retries with the new access token", async () => {
    const onRefresh = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ code: "AUTH_EXPIRED" }, 401))
      .mockResolvedValueOnce(jsonResponse({ access_token: "new-token" }))
      .mockResolvedValueOnce(jsonResponse({ account: { id: 1 } }));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test", onRefresh);
    api.setAccessToken("old-token");

    await expect(api.get("accounts/me")).resolves.toEqual({
      account: { id: 1 },
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://api.test/auth/refresh",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
    expect(fetchMock.mock.calls[2]?.[1]).toMatchObject({
      headers: { Authorization: "Bearer new-token" },
    });
    expect(onRefresh).toHaveBeenCalledWith("new-token");
  });

  it("coalesces concurrent refresh requests", async () => {
    let refreshCount = 0;
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith("/auth/refresh")) {
        refreshCount += 1;
        await Promise.resolve();
        return jsonResponse({ access_token: "new-token" });
      }
      const headers = options?.headers as Record<string, string>;
      return headers?.Authorization === "Bearer new-token"
        ? jsonResponse({ ok: true })
        : jsonResponse({ code: "AUTH_EXPIRED" }, 401);
    });
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");
    api.setAccessToken("old-token");

    await expect(
      Promise.all([api.get("accounts/me"), api.get("accounts/me")]),
    ).resolves.toEqual([{ ok: true }, { ok: true }]);
    expect(refreshCount).toBe(1);
  });

  it("does not refresh a failed login or retry after refresh failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ code: "INVALID_CREDENTIALS" }, 401))
      .mockResolvedValueOnce(jsonResponse({ code: "AUTH_EXPIRED" }, 401))
      .mockResolvedValueOnce(jsonResponse({ code: "REFRESH_EXPIRED" }, 401));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");

    await expect(api.post("auth/login", {})).rejects.toBeInstanceOf(HttpError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await expect(api.get("accounts/me")).rejects.toMatchObject({
      code: "AUTH_EXPIRED",
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("returns blobs and reports blob failures", async () => {
    const blob = new Blob(["file"]);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        blob: vi.fn().mockResolvedValue(blob),
        ok: true,
        status: 200,
      })
      .mockResolvedValueOnce(new Response(null, { status: 404 }));
    vi.stubGlobal("fetch", fetchMock);
    const api = new Api("http://api.test");

    await expect(api.getBlob("files/1")).resolves.toBeInstanceOf(Blob);
    await expect(api.getBlob("files/2", false)).rejects.toMatchObject({
      code: "BLOB_ERROR",
      status: 404,
    });
  });
});
