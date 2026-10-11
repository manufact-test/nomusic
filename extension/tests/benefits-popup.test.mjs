import assert from "node:assert/strict";
import test from "node:test";
import { initBenefitsPanel } from "../dist/unpacked/auth/benefits-popup.js";

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));
function fixture() {
  const nodes = new Map();
  for (const key of ["access", "payment", "code", "progress", "note", "create", "copy", "share", "refresh"])
    nodes.set(key, { textContent: "", hidden: false, handlers: {}, addEventListener(type, fn) { this.handlers[type] = fn; } });
  const root = { open: false, hidden: true, handlers: {},
    addEventListener(type, fn) { this.handlers[type] = fn; },
    querySelector(selector) { return nodes.get(selector.slice(15, -1)); } };
  return { root, nodes, document: { querySelector: () => root } };
}
const payload = { ok: true, entitlement: { allowed: true, source: "trial", valid_until: "2026-10-14T00:00:00Z" },
  referrals_available: true, referrals: { code: null, registered_count: 2 } };
test("Stage12 account screen requires an explicit code action and does not promise an earned discount", async () => {
  const previous = globalThis.document, fx = fixture(), calls = [];
  globalThis.document = fx.document;
  try {
    const panel = initBenefitsPanel(async (message) => {
      calls.push(message.action);
      return message.action === "referral-code" ? { ...payload, referrals: { ...payload.referrals, code: "A".repeat(32) } } : payload;
    });
    panel.signed(true); await tick(); assert.deepEqual(calls, ["benefits"], "signed in reads data without issuing a code");
    fx.root.open = true; fx.root.handlers.toggle(); await tick();
    assert.deepEqual(calls, ["benefits"]);
    assert.equal(fx.nodes.get("create").hidden, false);
    assert.match(fx.nodes.get("progress").textContent, /Зарегистрировались по коду: 2/);
    assert.equal(fx.nodes.get("note").hidden, true);
    fx.root.handlers.toggle(); await tick(); assert.deepEqual(calls, ["benefits"], "reopening does not refetch or flash loading text");
    fx.nodes.get("create").handlers.click(); await tick();
    assert.deepEqual(calls, ["benefits", "referral-code"]);
    assert.equal(fx.nodes.get("code").textContent, "A".repeat(32));
    assert.equal(fx.nodes.get("create").hidden, true);
    panel.signed(false); assert.equal(fx.root.hidden, true);
    assert.equal(fx.nodes.get("code").textContent, "");
  } finally { globalThis.document = previous; }
});
test("Stage12 logout prevents a delayed benefits response from repopulating another account screen", async () => {
  const previous = globalThis.document, fx = fixture(); globalThis.document = fx.document;
  try {
    let resolve; const pending = new Promise((done) => { resolve = done; });
    const panel = initBenefitsPanel(() => pending);
    panel.signed(true); fx.root.open = true; fx.root.handlers.toggle();
    panel.signed(false); resolve(payload); await tick();
    assert.equal(fx.nodes.get("progress").textContent, "");
    assert.equal(fx.root.hidden, true);
  } finally { globalThis.document = previous; }
});
test("disabled benefits show one explanation without duplicate access or inactive actions", async () => {
  const previous = globalThis.document, fx = fixture(); globalThis.document = fx.document;
  try {
    const panel = initBenefitsPanel(async () => ({ ok: true, referrals_available: false, referrals: null }));
    panel.signed(true); await tick();
    assert.equal(fx.nodes.get("progress").textContent, "Подписка и приглашения пока недоступны.");
    for (const key of ["code", "note", "create", "copy", "share"]) assert.equal(fx.nodes.get(key).hidden, true);
  } finally { globalThis.document = previous; }
});
