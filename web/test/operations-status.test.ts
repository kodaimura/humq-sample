import { describe, expect, it } from "vitest";

import { getOperationsStatusLabel } from "@lib/status";

describe("operations status labels", () => {
  it.each([
    ["PARTIALLY_ALLOCATED", "一部引当"],
    ["ALLOCATED", "引当済み"],
    ["PARTIALLY_SHIPPED", "一部出荷"],
    ["IN_TRANSIT", "移動中"],
    ["PAID", "入金済み"],
  ])("translates %s into Japanese", (status, expected) => {
    expect(getOperationsStatusLabel(status)).toBe(expected);
  });

  it("keeps unknown statuses readable", () => {
    expect(getOperationsStatusLabel("UNKNOWN_STATUS")).toBe("UNKNOWN STATUS");
  });
});
