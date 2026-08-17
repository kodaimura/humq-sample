import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PasswordConfirmationFields from "@features/PasswordConfirmationFields";
import PasswordInput from "@ui/PasswordInput";

describe("PasswordInput", () => {
  it("toggles visibility while preserving focus, selection, and scroll", async () => {
    render(<PasswordInput defaultValue="Password123!" id="password" />);
    const input = screen.getByDisplayValue("Password123!") as HTMLInputElement;
    const toggle = screen.getByRole("button", { name: "パスワードを表示" });
    input.focus();
    input.setSelectionRange(2, 8, "forward");
    input.scrollLeft = 12;

    fireEvent.pointerDown(toggle);
    fireEvent.click(toggle);

    expect(input).toHaveAttribute("type", "text");
    expect(toggle).toHaveAccessibleName("パスワードを非表示");
    expect(toggle).toHaveAttribute("aria-pressed", "true");
    await waitFor(() => {
      expect(input).toHaveFocus();
      expect(input.selectionStart).toBe(2);
      expect(input.selectionEnd).toBe(8);
      expect(input.scrollLeft).toBe(12);
    });

    fireEvent.click(toggle);
    expect(input).toHaveAttribute("type", "password");
  });

  it("disables both the input and visibility control", () => {
    render(<PasswordInput disabled id="password" />);
    expect(document.querySelector("input")).toBeDisabled();
    expect(screen.getByRole("button")).toBeDisabled();
  });
});

describe("PasswordConfirmationFields", () => {
  it("renders the reusable password contract and forwards changes", () => {
    const onPasswordChange = vi.fn();
    const onConfirmationChange = vi.fn();
    render(
      <PasswordConfirmationFields
        confirmationValue="Confirm123!"
        onConfirmationChange={onConfirmationChange}
        onPasswordChange={onPasswordChange}
        passwordValue="Password123!"
      />,
    );

    const password = document.querySelector<HTMLInputElement>("#password");
    const confirmation =
      document.querySelector<HTMLInputElement>("#confirm_password");
    expect(password).not.toBeNull();
    expect(confirmation).not.toBeNull();
    expect(password).toHaveAttribute("minlength", "8");
    expect(password).toHaveAttribute("name", "password");
    expect(confirmation).toHaveAttribute("name", "confirm_password");
    expect(screen.getByLabelText("ヘルプ")).toBeInTheDocument();

    fireEvent.change(password!, { target: { value: "changed" } });
    fireEvent.change(confirmation!, { target: { value: "changed" } });
    expect(onPasswordChange).toHaveBeenCalledOnce();
    expect(onConfirmationChange).toHaveBeenCalledOnce();
  });
});
