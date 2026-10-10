import assert from "node:assert/strict";
import test from "node:test";
import { initAuthPanel } from "../dist/unpacked/auth/auth-popup.js";

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

function fakePopup() {
  const nodes = new Map();
  function element(name) {
    const listeners = new Map();
    return {
      name, listeners, hidden: false, value: "", textContent: "", type: "text",
      dataset: {}, attributes: {}, autocomplete: "",
      addEventListener(type, fn) { listeners.set(type, fn); },
      setAttribute(name, value) { this.attributes[name] = value; },
      focus() { this.focused = true; },
      fire(type, additional = {}) { const listener = listeners.get(type); assert.ok(listener, name + ":" + type); return listener({ preventDefault() {}, ...additional }); }
    };
  }
  for (const name of ["panel","note","email","password","form","verify-form",
    "recovery-form","new-password-form","signed","summary","identity","submit",
    "mode","code","recovery-email","reset-code","reset-password","eye",
    "reset-eye","email-suggestion","resend","back","forgot","recovery-back","reset-back",
    "logout"]) nodes.set(name,element(name));
  nodes.get("password").type = "password";
  nodes.get("reset-password").type = "password";
  return { nodes, document: { querySelector(selector) {
    assert.match(selector, /^\[data-auth-[a-z-]+\]$/);
    return nodes.get(selector.slice(11,-1)) ?? null;
  } } };
}

test("Stage9 email verification survives actual popup close/reopen without stored passwords or codes", async () => {
  const oldDocument = globalThis.document;
  const oldChrome = globalThis.chrome;
  const memory = {};
  globalThis.chrome = { storage: { local: {
    async get(key) { return { [key]: memory[key] }; },
    async set(values) { Object.assign(memory, values); },
    async remove(key) { delete memory[key]; }
  } } };
  const send = async ({ action, ...payload }) => {
    if (action === "status") return { ok: true, available: true, signedIn: false };
    if (action === "register") return { ok: true, verification_required: true, email: payload.email };
    if (action === "verify-email") return { ok: true, user: { email: payload.email } };
    throw new Error("Unexpected action: " + action);
  };
  try {
    const first = fakePopup();
    globalThis.document = first.document;
    initAuthPanel(send);
    await tick();
    first.nodes.get("mode").fire("click");
    first.nodes.get("email").value = "owner@example.org";
    first.nodes.get("password").value = "temporary private password";
    first.nodes.get("form").fire("submit");
    await tick();
    assert.equal(first.nodes.get("verify-form").hidden, false);
    assert.deepEqual(memory["celikom-auth-pending-email"], {
      purpose: "verify", email: "owner@example.org"
    });
    assert.doesNotMatch(JSON.stringify(memory), /password|123456|access_token/);

    // Chrome destroys the popup DOM when the user switches to their mailbox.
    const reopened = fakePopup();
    globalThis.document = reopened.document;
    initAuthPanel(send);
    await tick();
    assert.equal(reopened.nodes.get("panel").open, true, "verification panel should reopen automatically");
    assert.equal(reopened.nodes.get("verify-form").hidden, false);
    assert.equal(reopened.nodes.get("form").hidden, true);
    reopened.nodes.get("code").value = "123456";
    reopened.nodes.get("verify-form").fire("submit");
    await tick();
    assert.equal(reopened.nodes.get("signed").hidden, false);
    assert.equal(memory["celikom-auth-pending-email"], undefined);
  } finally {
    globalThis.document = oldDocument;
    globalThis.chrome = oldChrome;
  }
});

test("Stage9 recovery email persists but one-time code and new password do not", async () => {
  const oldDocument = globalThis.document;
  const oldChrome = globalThis.chrome;
  const memory = {};
  globalThis.chrome = { storage: { local: {
    async get(key) { return { [key]: memory[key] }; },
    async set(values) { Object.assign(memory, values); },
    async remove(key) { delete memory[key]; }
  } } };
  const send = async ({ action }) => {
    if (action === "status") return { ok: true, available: true, signedIn: false };
    if (action === "request-reset" || action === "reset-password") return { ok: true };
    throw new Error("Unexpected action: " + action);
  };
  try {
    const first = fakePopup();
    globalThis.document = first.document;
    initAuthPanel(send);
    await tick();
    first.nodes.get("forgot").fire("click");
    first.nodes.get("recovery-email").value = "owner@example.org";
    first.nodes.get("recovery-form").fire("submit");
    await tick();
    assert.equal(first.nodes.get("new-password-form").hidden,false);
    assert.deepEqual(memory["celikom-auth-pending-email"], { purpose:"reset",email:"owner@example.org" });

    const reopened = fakePopup();
    globalThis.document = reopened.document;
    initAuthPanel(send);
    await tick();
    assert.equal(reopened.nodes.get("panel").open,true, "reset panel should reopen automatically");
    assert.equal(reopened.nodes.get("new-password-form").hidden,false);
    reopened.nodes.get("reset-code").value = "123456";
    reopened.nodes.get("reset-password").value = "a strong new password";
    reopened.nodes.get("new-password-form").fire("submit");
    await tick();
    assert.equal(memory["celikom-auth-pending-email"],undefined);
    assert.equal(reopened.nodes.get("form").hidden,false);
  } finally {
    globalThis.document = oldDocument;
    globalThis.chrome = oldChrome;
  }
});

test("Stage9 last verified account email is offered and selectable in the next popup", async () => {
  const oldDocument = globalThis.document;
  const oldChrome = globalThis.chrome;
  const memory = {};
  globalThis.chrome = { storage: { local: {
    async get(key) { return { [key]: memory[key] }; },
    async set(values) { Object.assign(memory, values); },
    async remove(key) { delete memory[key]; }
  } } };
  let signed = true;
  const send = async ({ action }) => {
    if (action === "status") return { available: true, signedIn: signed,
      user: signed ? { email: "remembered@example.org" } : undefined };
    if (action === "logout") return { ok: true };
    throw new Error("Unexpected action " + action);
  };
  try {
    const first = fakePopup(); globalThis.document = first.document;
    initAuthPanel(send);
    await tick();
    assert.equal(memory["celikom-auth-remembered-email"], "remembered@example.org");
    signed = false;
    const next = fakePopup(); globalThis.document = next.document;
    initAuthPanel(send);
    await tick();
    next.nodes.get("email").value = "rem";
    next.nodes.get("email").fire("input");
    assert.equal(next.nodes.get("email-suggestion").hidden, false);
    next.nodes.get("email").fire("keydown", {key:"ArrowDown"});
    // The keyboard shortcut must fill the field, not accidentally submit a form.
    assert.equal(next.nodes.get("email").value, "remembered@example.org");
    assert.equal(memory["celikom-auth-remembered-email"], "remembered@example.org");
    assert.doesNotMatch(JSON.stringify(memory), /refresh_token|access_token|password/);
  } finally {
    globalThis.document = oldDocument;
    globalThis.chrome = oldChrome;
  }
});
