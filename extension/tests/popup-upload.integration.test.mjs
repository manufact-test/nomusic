import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const elements = new Map();
function el(selector, values = {}) {
  const handlers = new Map();
  const node = { value: "", textContent: "", disabled: false, hidden: false, dataset: {},
    files: [], checked: false, title: "", ...values,
    addEventListener(name, fn) { handlers.set(name, fn); },
    async fire(name) { return handlers.get(name)?.({ preventDefault() {} }); } };
  elements.set(selector, node);
  return node;
}
for (const selector of ["[data-status]", "[data-action='start']", "[data-action='stop']",
  "[data-action='restore']", "[data-action='diagnostics']", "[data-track]", "[data-test-track]",
  "[data-upload-panel]", "[data-upload-track]", "[data-upload-file]", "[data-upload-key]",
  "[data-upload-rights]", "[data-upload-progress]", "[data-upload-status]", "[data-upload-submit]",
  "[data-upload-result]", "[data-upload-result-title]", "[data-upload-result-note]",
  "[data-action='add']", "[data-upload-form]"]) el(selector);
const find = (selector) => elements.get(selector);
find("[data-upload-panel]").hidden = true;
find("[data-upload-form]").hidden = true;
find("[data-upload-result]").hidden = true;
find("[data-upload-progress]").hidden = true;

const selected = { track: { id: "144530503", confidence: 200, ambiguous: false,
  metadata: { durationMs: 180872, title: "Owner fixture", artist: "CI" } } };
let current = selected, offline = false;
const pendingTracks = new Set();
const requests = [];
const statusCalls = [];
globalThis.document = { activeElement: null, querySelector: find };
globalThis.window = { setInterval() { return 1; } };
globalThis.chrome = {
  runtime: {
    getURL: (p) => "chrome-extension://ci-test/" + p,
    async sendMessage(message) {
      if (offline) throw new Error("simulated extension disconnect");
      if (message.type === "CELIKOM_STATUS_GET") return { ...current, phase: "READY", enabled: true };
      return { ok: true };
    }
  }
};
globalThis.fetch = async (url) => {
  if (String(url).includes("/api/v1/tracks/upload-status")) {
    statusCalls.push(String(url));
    const currentTrackId = new URL(String(url)).searchParams.get("track_id");
    return { ok: true, async json() { return { status: pendingTracks.has(currentTrackId) ? "pending" : "none" }; } };
  }
  return { ok: true, async json() { return { baseUrl: "https://isolated-owner-test.example/" }; } };
};
class FakeXHR {
  static throwOnSend = false;
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
    queueMicrotask(() => {
      pendingTracks.add(String(body.get("track_id")));
      this.listeners.get("loadend")?.();
    });
  }
}
globalThis.XMLHttpRequest = FakeXHR;
await import("../dist/unpacked/popup/popup.js");
await new Promise((resolve) => setImmediate(resolve));

function selection() {
  const file = new Blob([new Uint8Array(2500)], { type: "audio/mpeg" });
  Object.defineProperty(file, "name", { value: "owner.mp3" });
  find("[data-upload-file]").files = [file];
  find("[data-upload-rights]").checked = true;
  find("[data-upload-key]").value = "a-private-session-only-owner-token";
}
function form() { return find("[data-upload-form]"); }
function result() { return find("[data-upload-result]"); }

test("Stage 7 Add version pins exact Track ID, checks server, then shows form", async () => {
  const html = await readFile(new URL("../popup/popup.html", import.meta.url), "utf8");
  assert.match(html, /data-upload-track[^>]*readonly/);
  assert.match(html, /data-upload-result[^>]*hidden/);
  await find("[data-action='add']").fire("click");
  assert.equal(find("[data-upload-panel]").hidden, false);
  assert.equal(find("[data-upload-track]").value, "144530503");
  assert.equal(form().hidden, false);
  assert.equal(find("[data-upload-submit]").disabled, false);
  assert.ok(statusCalls.at(-1).includes("track_id=144530503"));
});

test("Stage 7 changed track during preparation never sends audio", async () => {
  selection();
  current = { track: { ...selected.track, id: "144530504" } };
  await form().fire("submit");
  assert.equal(requests.length, 0);
  assert.match(find("[data-upload-status]").textContent, /Трек изменился/);
});

test("Stage 7 extension status disconnect never sends audio", async () => {
  current = selected;
  offline = true;
  await form().fire("submit");
  assert.equal(requests.length, 0);
  assert.match(find("[data-upload-status]").textContent, /Не удалось связаться/);
  offline = false;
});

test("Stage 7 synchronous network error does not strand disabled submit", async () => {
  FakeXHR.throwOnSend = true;
  await form().fire("submit");
  assert.equal(requests.length, 1);
  assert.equal(find("[data-upload-submit]").disabled, false);
  assert.match(find("[data-upload-status]").textContent, /Не удалось связаться/);
  FakeXHR.throwOnSend = false;
});

test("Stage 7 accepted upload displays unmistakable confirmation and locks controls", async () => {
  await form().fire("submit");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(requests.length, 2);
  assert.equal(requests.at(-1).method, "POST");
  assert.equal(requests.at(-1).url, "https://isolated-owner-test.example/api/v1/uploads");
  assert.equal(requests.at(-1).headers.get("Authorization"), "Bearer a-private-session-only-owner-token");
  assert.equal(requests.at(-1).body.get("track_id"), "144530503");
  assert.equal(requests.at(-1).body.get("duration_ms"), "180872");
  assert.equal(requests.at(-1).body.get("declaration"), "1");
  assert.equal(requests.at(-1).body.get("service"), "yandex");
  assert.ok(/^[a-f0-9-]{36}$/.test(requests.at(-1).body.get("request_id")));
  assert.equal(form().hidden, true);
  assert.equal(result().hidden, false);
  assert.match(find("[data-upload-result-title]").textContent, /Отправлено на проверку/);
  assert.equal(find("[data-upload-submit]").disabled, true);
  assert.equal(find("[data-upload-key]").value, "", "owner token wiped from DOM");
  await form().fire("submit");
  assert.equal(requests.length, 2, "click again cannot upload");
});

test("Stage 7 reopening popup-equivalent panel sees server pending without bearer", async () => {
  await find("[data-action='add']").fire("click"); // close
  await find("[data-action='add']").fire("click"); // open, query server again
  assert.equal(form().hidden, true);
  assert.equal(result().hidden, false);
  assert.match(find("[data-upload-result-title]").textContent, /Трек уже добавлен/);
  assert.match(find("[data-upload-result-note]").textContent, /ожидает проверки/);
  assert.equal(requests.length, 2);
});

test("Stage 7 on another Track ID remains eligible and rejects unconfirmed rights", async () => {
  current = { track: { ...selected.track, id: "144530505" } };
  await find("[data-action='add']").fire("click");
  await find("[data-action='add']").fire("click");
  assert.equal(find("[data-upload-track]").value, "144530505");
  assert.equal(form().hidden, false);
  find("[data-upload-rights]").checked = false;
  await form().fire("submit");
  assert.equal(requests.length, 2);
});
