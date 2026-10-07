import assert from "node:assert/strict";
import test from "node:test";
import { COMMANDS, isCommand, normalizeEnabled } from "../dist/unpacked/shared/messages.js";

test("command names stay explicit and namespaced", () => {
  for (const command of Object.values(COMMANDS)) {
    assert.match(command, /^CELIKOM_[A-Z_]+$/);
    assert.equal(isCommand(command), true);
  }
});

test("enabled state fails closed for non-boolean values", () => {
  assert.equal(normalizeEnabled(true), true);
  for (const value of [false, 1, "true", null, undefined, {}]) {
    assert.equal(normalizeEnabled(value), false);
  }
});
