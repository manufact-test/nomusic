import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../popup/popup.html",import.meta.url),"utf8");
const css = await readFile(new URL("../popup/popup.css",import.meta.url),"utf8");
const script = await readFile(new URL("../src/auth/auth-popup.ts",import.meta.url),"utf8");

test("Stage9 account uses inline validation and accessible code confirmation", () => {
  for (const part of ["data-auth-form", "data-auth-verify-form", "data-auth-recovery-form",
    "data-auth-new-password-form"]) assert.match(html,new RegExp(part+'[^>]*novalidate'));
  assert.match(html,/data-auth-email[^>]*name="username"[^>]*autocomplete="username"/);
  assert.match(html,/data-auth-email-suggestion[^>]*type="button"/);
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

test("Stage9 title is white; both password eyes use identical SVG shapes", () => {
  assert.match(css,/\.account-panel > summary\s*\{[^}]*color:\s*#ffffff/);
  const svg = '<svg viewBox="0 0 24 24" width="18" height="18"';
  assert.equal(html.split(svg).length - 1, 2, "matching eye icons in login and password reset");
  assert.doesNotMatch(html,/>👁<\/button>/);
});
test("Stage9 auth screen keeps a stable inner scroll region rather than resizing popup", () => {
  assert.match(css,/\.account-panel\[open\]:not\(\[data-auth-screen="signed"\]\) \.account-content/);
  assert.match(css,/overscroll-behavior:\s*contain/);
  assert.match(script,/root\.dataset\.authScreen = next/);
  assert.match(script,/content\.scrollTop = 0/);
});
test("Stage9 remembered email is local to extension and can be chosen by keyboard or click", () => {
  assert.match(script,/celikom-auth-remembered-email/);
  assert.match(script,/remember\(state\.user\?\.email\)/);
  assert.match(script,/\["ArrowDown", "Enter"\]/);
  assert.match(script,/pointerdown/);
  assert.doesNotMatch(script,/\[pendingKey\]:\s*\{[^}]*password/);
});
