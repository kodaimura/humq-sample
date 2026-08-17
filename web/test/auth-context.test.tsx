import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  setAccessToken: vi.fn(),
  setAccessTokenCallback: vi.fn(),
}));

vi.mock("@lib/api", () => ({ api: apiMock }));

import { AuthProvider, useAuth } from "@contexts/AuthContext";

const account = {
  created_at: "2026-01-01T00:00:00Z",
  disabled_at: null,
  email: "user@example.com",
  first_name: "Test",
  id: 1,
  last_name: "User",
  login_id: "user@example.com",
  updated_at: "2026-01-01T00:00:00Z",
};

const Consumer = () => {
  const auth = useAuth();
  return (
    <div>
      <span>
        {auth.loading ? "loading" : auth.account?.login_id || "anonymous"}
      </span>
      <span>{auth.accessToken || "no-token"}</span>
      <button onClick={() => auth.setAccessToken("manual-token")}>
        set token
      </button>
      <button onClick={auth.logout}>logout</button>
    </div>
  );
};

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMock.get.mockResolvedValue({ account });
    apiMock.post.mockResolvedValue({});
  });

  it("restores the current account and wires refreshed access tokens", async () => {
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    expect(screen.getByText("loading")).toBeInTheDocument();
    expect(await screen.findByText("user@example.com")).toBeInTheDocument();
    expect(apiMock.get).toHaveBeenCalledWith("/accounts/me");
    expect(apiMock.setAccessTokenCallback).toHaveBeenCalledWith(
      expect.any(Function),
    );

    const refreshCallback = apiMock.setAccessTokenCallback.mock.calls[0]?.[0];
    refreshCallback("refreshed-token");
    expect(await screen.findByText("refreshed-token")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "set token" }));
    await waitFor(() =>
      expect(apiMock.setAccessToken).toHaveBeenLastCalledWith("manual-token"),
    );
  });

  it("finishes initialization as anonymous when account restoration fails", async () => {
    apiMock.get.mockRejectedValue(new Error("offline"));
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    expect(await screen.findByText("anonymous")).toBeInTheDocument();
  });

  it("keeps local logout successful when the server request fails", async () => {
    apiMock.post.mockRejectedValue(new Error("offline"));
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );
    expect(await screen.findByText("user@example.com")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "logout" }));

    expect(await screen.findByText("anonymous")).toBeInTheDocument();
    expect(apiMock.post).toHaveBeenCalledWith("/auth/logout");
    await waitFor(() =>
      expect(apiMock.setAccessToken).toHaveBeenLastCalledWith(null),
    );
  });

  it("rejects use outside its provider", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() => render(<Consumer />)).toThrow(
      "useAuth must be used within an AuthProvider",
    );
  });
});
