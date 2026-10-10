import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../popup/popup.html",import.meta.url),"utf8");
const css = await readFile(new URL("../popup/popup.css",import.meta.url),"utf8");
const script = await readFile(new URL("../src/auth/auth-popup.ts",import.meta.url),"utf8");

test("Stage9 account uses inline validation and accessible code confirmation", () => {
  for (const part of ["data-auth-form", "data-auth-verify-form", "data-auth-recovery-form",
    "data-auth-new-password-form"]) assert.match(html,new RegExp(part+'[^>]*novalidate'));
  assert.match(html,/data-auth-email[^>]*autocomplete="email"/);
  assert.match(html,/data-auth-code[^>]*autocomplete="one-time-code"/);
  assert.match(html,/data-auth-note[^>]*aria-live="polite"/);
  assert.doesNotMatch(html,/data-auth-list-devices|data-auth-devices/);
});
test("Stage9 password visibility has keyboard controls and accessibility labels", () => {
  assert.match(html,/data-auth-eye[^>]*type="button"[^>]*aria-label="Показать пароль"/);
  assert.match(html,/data-auth-reset-eye[^>]*type="button"[^>]*aria-label="Показать пароль"/);
  assert.match(script,/aria-pressed/);
  assert.match(script,/input\.focus\(\)/);
});
test("Stage9 focus highlights actual border rather than drawing a detached halo", () => {
  assert.match(css,/\.account-form input:focus\s*\{[^}]*border-color:\s*#66e0bf/);
  assert.match(css,/button:focus-visible, input:focus-visible, summary:focus-visible\s*\{[^}]*outline:\s*none/);
  assert.doesNotMatch(css,/outline-offset:\s*3px/);
});
test("Stage9 error presentation and logout remain separate from owner uploads", () => {
  assert.match(css,/\.auth-feedback\[data-kind="error"\]/);
  assert.match(script,/invalid_credentials/);
  assert.match(script,/resend-verification/);
  assert.match(script,/reset-password/);
  assert.match(html,/data-upload-form/);
});
