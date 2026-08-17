import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AppRouter from "@/AppRouter";

const { useAuthMock } = vi.hoisted(() => ({
  useAuthMock: vi.fn(),
}));

vi.mock("@contexts/AuthContext", () => ({ useAuth: useAuthMock }));

const signedInAccount = {
  id: 1,
  login_id: "user@example.com",
};

describe("reset password route", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/reset-password?token=reset-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({}), {
          headers: { "Content-Type": "application/json" },
          status: 200,
        }),
      ),
    );
  });

  it.each([
    ["signed out", null],
    ["signed in", signedInAccount],
  ])("renders while %s", async (_state, account) => {
    useAuthMock.mockReturnValue({
      accessToken: null,
      account,
      loading: false,
      logout: vi.fn(),
      setAccessToken: vi.fn(),
      setAccount: vi.fn(),
    });

    render(<AppRouter />);

    expect(
      await screen.findByRole("heading", { name: "新しいパスワード" }),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "auth/reset-password/verify?token=reset-token",
        ),
        expect.any(Object),
      ),
    );
  });
});
