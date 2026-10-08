import assert from "node:assert/strict";
import test from "node:test";
import { ApiClient } from "../dist/unpacked/api/api-client.js";
import { validateApiAccess } from "../dist/unpacked/api/api-access-validation.js";
import { createApiBroker } from "../dist/unpacked/api/api-broker.js";
import { apiBuildConfig } from "../scripts/api-build-config.mjs";

const config = { api_version: 1, minimum_extension_version: "0.4.0", maintenance: false, features: { replacements: true, analytics: false } };
const now = 1791478000000;
const found = { found: true, replacement_id: 7, version: 1, duration_ms: 201000, expires_at: now / 1000 + 600, audio_url: `/api/v1/audio/7?token=${"a".repeat(64)}&expires=${now / 1000 + 600}` };
const response = (value) => new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } });

test("API cache coalesces exact-ID requests and bounds positive/negative expiry", async () => {
  let calls = 0; let time = now;
  const client = new ApiClient("https://celikom.example", { now: () => time, fetch: async (url) => { calls++; return response(url.endsWith("config") ? config : url.includes("track_id=7") ? found : { found: false }); } });
  const [a, b] = await Promise.all([client.resolve("yandex", "7"), client.resolve("yandex", "7")]);
  assert.equal(a.replacementId, 7); assert.equal(a, b); assert.equal(calls, 2);
  await client.resolve("yandex", "7"); assert.equal(calls, 2);
  await client.resolve("yandex", "8"); await client.resolve("yandex", "8"); assert.equal(calls, 3);
  time += 16000; await client.resolve("yandex", "8"); assert.equal(calls, 4);
  time += 120000; await client.resolve("yandex", "7"); assert.equal(calls, 6);
});

test("API URL validation rejects foreign origin, filesystem paths, forged IDs and stale tokens", async () => {
  for (const update of [
    { audio_url: "https://evil.example/api/v1/audio/7" },
    { audio_url: "/storage/private.mp3" }, { audio_url: found.audio_url.replace("audio/7", "audio/8") },
    { expires_at: now / 1000 - 1 }, { found: true, replacement_id: "7" },
    { audio_url: found.audio_url + "&filename=private" }
  ]) {
    const client = new ApiClient("https://celikom.example", { now: () => now, fetch: async (url) => response(url.endsWith("config") ? config : { ...found, ...update }) });
    await assert.rejects(client.resolve("yandex", "7"));
  }
  for (const origin of ["http://celikom.example", "https://user:pass@celikom.example", "https://celikom.example/private", "file:///tmp/api"]) assert.throws(() => new ApiClient(origin));
  assert.equal(apiBuildConfig("http://127.0.0.1:8080").baseUrl, "http://127.0.0.1:8080");
  assert.throws(() => apiBuildConfig("http://celikom.example"));
});

test("maintenance and minimum version suppress resolve; failures do not become positive cache", async () => {
  for (const update of [{ maintenance: true }, { features: { replacements: false } }]) {
    let calls = 0;
    const client = new ApiClient("https://celikom.example", { fetch: async () => { calls++; return response({ ...config, ...update }); } });
    assert.equal((await client.resolve("yandex", "7")).found, false); assert.equal(calls, 1);
  }
  const outdated = new ApiClient("https://celikom.example", { fetch: async () => response({ ...config, minimum_extension_version: "0.5.0" }) });
  await assert.rejects(outdated.resolve("yandex", "7"), /update_required/);
  let fail = true; let calls = 0;
  const client = new ApiClient("https://celikom.example", { now: () => now, fetch: async (url) => { calls++; if (!url.endsWith("config") && fail) return new Response("error", { status: 500 }); return response(url.endsWith("config") ? config : found); } });
  await assert.rejects(client.resolve("yandex", "7")); fail = false;
  assert.equal((await client.resolve("yandex", "7")).found, true); assert.equal(calls, 3);
});

test("API body and content type are bounded before parsing", async () => {
  for (const fetcher of [async () => new Response("html"), async () => new Response(" ".repeat(65537), { headers: { "Content-Type": "application/json" } })]) {
    const client = new ApiClient("https://celikom.example", { fetch: fetcher });
    await assert.rejects(client.resolve("yandex", "7"));
  }
});

test("worker broker exposes no arbitrary fetch or access token to content", async () => {
  let calls = 0;
  const api = { runtime: { id: "extension-test", getManifest: () => ({ version: "0.4.0" }) }, storage: { local: { get: async () => ({ apiTestToken: "private-test-access" }) } } };
  const broker = createApiBroker(api, { now: () => now, readConfig: async () => ({ baseUrl: "https://celikom.example" }), fetch: async (url, options) => { calls++; assert.equal(options.credentials, "omit"); assert.equal(options.headers.Authorization, "Bearer private-test-access"); return response(url.endsWith("config") ? config : found); } });
  const message = { type: "CELIKOM_API_RESOLVE", service: "yandex", trackId: "7", url: "https://evil.example" };
  for (const sender of [{ id: "other", url: "https://music.yandex.ru" }, { id: "extension-test", url: "https://evil.example" }, { id: "extension-test", url: "invalid" }]) assert.equal((await broker(message, sender)).ok, false);
  assert.equal(calls, 0);
  const result = await broker(message, { id: "extension-test", url: "https://music.yandex.ru/landing/main" });
  assert.equal(result.asset.replacementId, 7); assert.equal(calls, 2);
  assert.equal(JSON.stringify(result).includes("private-test-access"), false);
  const unconfigured = createApiBroker(api, { readConfig: async () => ({ baseUrl: "" }) });
  assert.equal((await unconfigured(message, { id: "extension-test", url: "https://music.yandex.ru" })).configured, false);
});

test("safe authentication diagnosis distinguishes a missing token, HTTP 401, and network failures", async () => {
  const api = {
    runtime: { id: "ext-diagnosis", getManifest: () => ({ version: "0.4.0" }) },
    storage: { local: { get: async () => ({ apiTestToken: "" }) } }
  };
  const sender = { id: "ext-diagnosis", url: "https://music.yandex.ru/album/38902809/track/144530503" };
  const request = { type: "CELIKOM_API_RESOLVE", service: "yandex", trackId: "144530503" };
  const missing = createApiBroker(api, { readConfig: async () => ({ baseUrl: "https://celikom.example" }) });
  assert.equal((await missing(request, sender)).error, "api_access_missing");

  api.storage.local.get = async () => ({ apiTestToken: "a".repeat(40) });
  const unauthorized = createApiBroker(api, {
    readConfig: async () => ({ baseUrl: "https://celikom.example" }),
    fetch: async url => url.endsWith("config") ? response(config) : new Response('{"error":"unauthorized"}', { status: 401, headers: { "Content-Type": "application/json" } })
  });
  const denied = await unauthorized(request, sender);
  assert.equal(denied.error, "api_access_denied");
  assert.equal(JSON.stringify(denied).includes("a".repeat(40)), false);

  const unreachable = createApiBroker(api, {
    readConfig: async () => ({ baseUrl: "https://celikom.example" }),
    fetch: async () => { throw new Error("A SECRET THAT MUST NOT BE SENT TO PAGE"); }
  });
  const network = await unreachable(request, sender);
  assert.equal(network.error, "api_network_error");
  assert.equal(JSON.stringify(network).includes("SECRET"), false);
});

test("popup verifies real server authorization before storing a private token", async () => {
  const api = { runtime: { id: "ext-test", getURL: path => "chrome-extension://ext-test/" + path, getManifest: () => ({ version: "0.4.0" }) } };
  const token = "verified-token".repeat(4);
  const base = { readConfig: async () => ({ baseUrl: "https://celikom.example" }) };
  const invalid = await validateApiAccess(api, token, {
    ...base, fetch: async (_url, opts) => {
      assert.equal(opts.headers.Authorization, "Bearer " + token);
      return new Response('{"error":"unauthorized"}', { status: 401, headers: { "Content-Type": "application/json" } });
    }
  });
  assert.deepEqual(invalid, { ok: false, error: "api_access_denied" });

  const valid = await validateApiAccess(api, " " + token + " ", {
    ...base, fetch: async (_url, opts) => {
      assert.equal(opts.headers.Authorization, "Bearer " + token);
      return response({ found: false });
    }
  });
  assert.deepEqual(valid, { ok: true, token });
  assert.deepEqual(await validateApiAccess(api, "too-short", base), { ok: false, error: "invalid_access_code" });
});

test("native worker fetch retains its Web IDL receiver (regression: silent api_network_error)", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  try {
    globalThis.fetch = function strictWorkerFetch(_url, _options) {
      assert.equal(this, globalThis, "native fetch must be bound to WorkerGlobalScope, not ApiClient");
      calls += 1;
      return Promise.resolve(new Response('{"error":"unauthorized"}', {
        status: 401, headers: { "Content-Type": "application/json" }
      }));
    };
    const client = new ApiClient("https://celikom.example", { accessToken: "fake-test-credential" });
    await assert.rejects(client.request("/api/v1/resolve?service=yandex&track_id=1"), /api_access_denied/);
    assert.equal(calls, 1, "request must reach fetch instead of throwing before a network call");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
