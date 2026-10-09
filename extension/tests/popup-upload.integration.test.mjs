import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const events = new Map();
function el(selector, values = {}) {
  const handlers = new Map();
  const node = { value: "", textContent: "", disabled: false, hidden: false, dataset: {},
    files: [], checked: false, title: "", ...values,
    addEventListener(name, fn) { handlers.set(name, fn); },
    async fire(name) { await handlers.get(name)?.({ preventDefault() {} }); } };
  events.set(selector, node);
  return node;
}
for (const selector of ["[data-status]", "[data-action='start']", "[data-action='stop']",
  "[data-action='restore']", "[data-action='diagnostics']", "[data-track]", "[data-test-track]",
  "[data-upload-panel]", "[data-upload-track]", "[data-upload-file]", "[data-upload-key]",
  "[data-upload-rights]", "[data-upload-progress]", "[data-upload-status]", "[data-upload-submit]",
  "[data-action='add']", "[data-upload-form]"]) el(selector);
const find = (selector) => events.get(selector);
// Reflect the HTML 'hidden' attribute on the initially closed Add version panel.
events.get("[data-upload-panel]").hidden = true;
const selected = { track: { id: "144530503", confidence: 200, ambiguous: false,
  metadata: { durationMs: 180872, title: "Owner fixture", artist: "CI" } } };
let current = selected, offline = false, requests = [];
globalThis.document = {
  activeElement: null,
  querySelector: find,
};
globalThis.window = { setInterval() { return 1; } };
globalThis.chrome = {
  runtime: {
    getURL: (p) => "chrome-extension://ci-test/" + p,
    async sendMessage(message) {
      if (offline) throw new Error("simulated extension disconnect");
      if (message.type === "CELIKOM_STATUS_GET") return { ...current, phase: "READY", enabled: true };
      return { ok: true };
    },
  },
};
globalThis.fetch = async () => ({ async json() {
  return { baseUrl: "https://isolated-owner-test.example/" };
} });
class FakeXHR {
  constructor() {
    this.status = 202;
    this.responseText = JSON.stringify({ status: "pending", replacement_id: 71, duplicate: false });
    this.listeners = new Map();
    this.upload = { addEventListener() {} };
  }
  open(method, url) { this.method = method; this.url = url; }
  setRequestHeader(name, value) { this.headers ||= new Map(); this.headers.set(name, value); }
  addEventListener(name, cb) { this.listeners.set(name, cb); }
  send(body) {
    requests.push({ method: this.method, url: this.url, headers: this.headers, body });
    if (FakeXHR.throwOnSend) throw new Error("network startup denied");
    queueMicrotask(() => this.listeners.get("loadend")?.());
  }
}
globalThis.XMLHttpRequest = FakeXHR;
await import("../dist/unpacked/popup/popup.js");
await new Promise((resolve) => setImmediate(resolve));

test("Stage 7 Add version pins the exact detected Track ID without an editable field", async () => {
  const html = await readFile(new URL("../popup/popup.html", import.meta.url), "utf8");
  assert.match(html, /data-upload-track[^>]*readonly/);
  await find("[data-action='add']").fire("click");
  assert.equal(find("[data-upload-panel]").hidden, false);
  assert.equal(find("[data-upload-track]").value, "144530503");
  assert.equal(find("[data-upload-submit]").disabled, false);
});

test("Stage 7 popup owner upload carries pinned metadata, rights, and a transient token", async () => {
  const file = new Blob([new Uint8Array(2500)], { type: "audio/mpeg" });
  Object.defineProperty(file, "name", { value: "owner.mp3" });
  find("[data-upload-file]").files = [file];
  find("[data-upload-rights]").checked = true;
  find("[data-upload-key]").value = "a-private-session-only-owner-token";
  await find("[data-upload-form]").fire("submit");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(requests.length, 1);
  assert.equal(requests[0].method, "POST");
  assert.equal(requests[0].url, "https://isolated-owner-test.example/api/v1/uploads");
  assert.equal(requests[0].headers.get("Authorization"), "Bearer a-private-session-only-owner-token");
  const form = requests[0].body;
  assert.equal(form.get("track_id"), "144530503");
  assert.equal(form.get("duration_ms"), "180872");
  assert.equal(form.get("declaration"), "1");
  assert.equal(form.get("service"), "yandex");
  assert.ok(/^[0-9a-f-]{36}$/.test(form.get("request_id")));
  assert.match(find("[data-upload-status]").textContent, /Ожидает ручной проверки/);
});

test("Stage 7 fails closed when track changes during preparation", async () => {
  current = { track: { ...selected.track, id: "144530504" } };
  await find("[data-upload-form]").fire("submit");
  assert.equal(requests.length, 1);
  assert.match(find("[data-upload-status]").textContent, /Трек изменился/);
});

test("Stage 7 status disconnect does not create an accidental upload", async () => {
  current = selected;
  offline = true;
  await find("[data-upload-form]").fire("submit");
  assert.equal(requests.length, 1);
  assert.match(find("[data-upload-status]").textContent, /Не удалось определить/);
  offline = false;
});

test("Stage 7 disabled/conflicting sender and failed XHR cannot strand upload UI", async () => {
  FakeXHR.throwOnSend = true;
  await find("[data-upload-form]").fire("submit");
  assert.equal(requests.length, 2);
  assert.equal(find("[data-upload-submit]").disabled, false);
  assert.match(find("[data-upload-status]").textContent, /Не удалось начать/);
  FakeXHR.throwOnSend = false;
  find("[data-upload-rights]").checked = false;
  await find("[data-upload-form]").fire("submit");
  assert.equal(requests.length, 2);
});
