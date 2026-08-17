import assert from "node:assert/strict";
import test from "node:test";
import { ApiClient, expectStatus } from "./support.mjs";

test("health endpoint reports API readiness", async () => {
  const client = new ApiClient();
  const response = expectStatus(await client.get("/health"), 200, "health");
  assert.equal(response.json?.status, "ok");
});
