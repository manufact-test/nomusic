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

test("Stage 6: two installations independently refresh negative cache after an approve", async () => {
  let time = now; let approved = false; let resolveCalls = 0;
  const server = async (url) => {
    if (url.endsWith("/api/v1/config")) return response(config);
    resolveCalls++;
    assert.match(url, /track_id=888$/);
    const expires = Math.floor(time / 1000) + 600;
    return response(approved ? {
      found: true, replacement_id: 31, version: 1, duration_ms: 201000,
      expires_at: expires,
      audio_url: "/api/v1/audio/31?token=" + "b".repeat(64) + "&expires=" + expires
    } : { found: false, cache_ttl_seconds: 15 });
  };
  const first = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  const second = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  assert.equal((await first.resolve("yandex", "888")).found, false);
  assert.equal((await second.resolve("yandex", "888")).found, false);
  approved = true;
  assert.equal((await first.resolve("yandex", "888")).found, false);
  assert.equal((await second.resolve("yandex", "888")).found, false);
  assert.equal(resolveCalls, 2, "no resolve polling within TTL");
  time += 15001;
  assert.equal((await first.resolve("yandex", "888")).replacementId, 31);
  assert.equal((await second.resolve("yandex", "888")).replacementId, 31);
  assert.equal(resolveCalls, 4, "both clients refresh once");
});

test("Stage 6: positive cache sees server-side active mapping switch after TTL", async () => {
  let time = now; let current = 41; let resolves = 0;
  const server = async (url) => {
    if (url.endsWith("/api/v1/config")) return response(config);
    resolves++;
    assert.match(url, /track_id=777$/);
    const expires = Math.floor(time / 1000) + 600;
    return response({
      found: true, replacement_id: current, version: 1, duration_ms: 201000,
      expires_at: expires,
      audio_url: "/api/v1/audio/" + current + "?token=" + "c".repeat(64) + "&expires=" + expires
    });
  };
  const client = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  assert.equal((await client.resolve("yandex", "777")).replacementId, 41);
  current = 42;
  assert.equal((await client.resolve("yandex", "777")).replacementId, 41);
  assert.equal(resolves, 1);
  time += 120001;
  assert.equal((await client.resolve("yandex", "777")).replacementId, 42);
  assert.equal((await client.resolve("yandex", "777")).replacementId, 42);
  assert.equal(resolves, 2, "no unnecessary retry");
});

test("Stage 6.5: server TTL config governs negative approval discovery and positive refresh", async () => {
  let time = now; let approved = false; let replacementId = 81; let calls = 0;
  const updatedConfig = { ...config, resolve_cache_ttl_seconds: 7, negative_cache_ttl_seconds: 5 };
  const server = async (url) => {
    if (url.endsWith("/api/v1/config")) return response(updatedConfig);
    calls++;
    if (!approved) return response({ found: false, cache_ttl_seconds: 5 });
    const expires = Math.floor(time / 1000) + 600;
    return response({ found: true, replacement_id: replacementId, version: 1, duration_ms: 201000,
      expires_at: expires, cache_ttl_seconds: 7,
      audio_url: "/api/v1/audio/" + replacementId + "?token=" + "d".repeat(64) + "&expires=" + expires });
  };
  const client = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  assert.equal((await client.resolve("yandex", "222")).retryAfterMs, 5000);
  approved = true;
  time += 4999;
  assert.equal((await client.resolve("yandex", "222")).found, false);
  assert.equal(calls, 1, "pending approval uses negative TTL, not polling");
  time += 2;
  assert.equal((await client.resolve("yandex", "222")).replacementId, 81);
  assert.equal(calls, 2);
  replacementId = 82;
  time += 6999;
  assert.equal((await client.resolve("yandex", "222")).replacementId, 81);
  assert.equal(calls, 2);
  time += 2;
  assert.equal((await client.resolve("yandex", "222")).replacementId, 82);
  assert.equal(calls, 3, "new approved mapping visible after server positive TTL");
});
test("Stage 6.5: signed expiry bounds positive cache and invalid TTLs cannot bypass validation", async () => {
  let time = now; let calls = 0;
  const validConfig = { ...config, resolve_cache_ttl_seconds: 120, negative_cache_ttl_seconds: 60 };
  const client = new ApiClient("https://celikom.example", { now: () => time, fetch: async url => {
    if (url.endsWith("/api/v1/config")) return response(validConfig);
    calls++;
    const expires = Math.floor(time / 1000) + 40;
    return response({ found: true, replacement_id: 7, version: 1, duration_ms: 201000, expires_at: expires,
      cache_ttl_seconds: 120,
      audio_url: "/api/v1/audio/7?token=" + "e".repeat(64) + "&expires=" + expires });
  } });
  await client.resolve("yandex", "7");
  time += 10001;
  await client.resolve("yandex", "7");
  assert.equal(calls, 2, "signed token 30s safety margin limits positive cache");
  for (const ttl of ["15", null, 1.5]) {
    const bad = new ApiClient("https://celikom.example", { now: () => now, fetch: async url =>
      response(url.endsWith("/api/v1/config") ? config : { found: false, cache_ttl_seconds: ttl }) });
    await assert.rejects(bad.resolve("yandex", "8"), /invalid_api_response/);
  }
  const badConfig = new ApiClient("https://celikom.example", { fetch: async () =>
    response({ ...config, negative_cache_ttl_seconds: "5" }) });
  await assert.rejects(badConfig.resolve("yandex", "8"), /invalid_api_config/);
  let offline = true; let requests = 0;
  const outage = new ApiClient("https://celikom.example", { now: () => now, fetch: async url => {
    if (url.endsWith("/api/v1/config")) return response(config);
    requests++;
    if (offline) throw new Error("network disconnected");
    return response({ found: false, cache_ttl_seconds: 15 });
  } });
  await assert.rejects(outage.resolve("yandex", "8"), /api_network_error/);
  offline = false;
  assert.equal((await outage.resolve("yandex", "8")).found, false);
  assert.equal(requests, 2, "failure must not enter cache");
});
test("Stage 6.6: independent clients agree on shared approved mapping, then fail open after disable TTL", async () => {
  let time = now; let active = true; let attempts = 0;
  const configuration = { ...config, resolve_cache_ttl_seconds: 5, negative_cache_ttl_seconds: 5 };
  const server = async (url) => {
    if (url.endsWith("/api/v1/config")) return response(configuration);
    attempts++;
    if (!active) return response({ found: false, cache_ttl_seconds: 5 });
    const expires = Math.floor(time / 1000) + 600;
    return response({
      found: true, replacement_id: 101, version: 8, duration_ms: 201000,
      cache_ttl_seconds: 5, expires_at: expires,
      audio_url: "/api/v1/audio/101?token=" + "c".repeat(64) + "&expires=" + expires
    });
  };
  const alpha = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  const beta = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  const [first, second] = await Promise.all([
    alpha.resolve("yandex", "900002"), beta.resolve("yandex", "900002")
  ]);
  assert.equal(first.replacementId, 101);
  assert.equal(second.replacementId, 101, "same shared catalog mapping across installations");
  assert.equal(attempts, 2, "one request per client, without shared local cache");
  for (let i = 0; i < 20; i++) {
    assert.equal((await alpha.resolve("yandex", "900002")).replacementId, 101);
    assert.equal((await beta.resolve("yandex", "900002")).replacementId, 101);
  }
  assert.equal(attempts, 2, "no per-tick polling");
  active = false;
  time += 5001;
  const [lostA, lostB] = await Promise.all([
    alpha.resolve("yandex", "900002"), beta.resolve("yandex", "900002")
  ]);
  assert.equal(lostA.found, false, "disabled mapping falls back to original");
  assert.equal(lostB.found, false, "other installation also falls back to original");
  assert.equal(lostA.retryAfterMs, 5000);
  assert.equal(attempts, 4, "one refresh per installation on expiry");
  await Promise.all([alpha.resolve("yandex", "900002"), beta.resolve("yandex", "900002")]);
  assert.equal(attempts, 4, "disabled mapping is negatively cached");
});

test("Stage 6.6: different exact Track IDs do not share cached resolution identity", async () => {
  let time = now; const counts = new Map();
  const server = async (url) => {
    if (url.endsWith("/api/v1/config")) return response(config);
    const id = new URL(url).searchParams.get("track_id");
    counts.set(id, (counts.get(id) || 0) + 1);
    if (id === "999998") return response({ found: false, cache_ttl_seconds: 15 });
    const replacement = id === "900003" ? 103 : 104;
    const expires = Math.floor(time / 1000) + 600;
    return response({
      found: true, replacement_id: replacement, version: 1, duration_ms: 201000,
      cache_ttl_seconds: 30, expires_at: expires,
      audio_url: "/api/v1/audio/" + replacement + "?token=" + "a".repeat(64) + "&expires=" + expires
    });
  };
  const client = new ApiClient("https://celikom.example", { now: () => time, fetch: server });
  const [a, b, unknown] = await Promise.all([
    client.resolve("yandex", "900003"), client.resolve("yandex", "900004"), client.resolve("yandex", "999998")
  ]);
  assert.equal(a.replacementId, 103);
  assert.equal(b.replacementId, 104);
  assert.equal(unknown.found, false);
  assert.deepEqual(Object.fromEntries(counts), { "900003": 1, "900004": 1, "999998": 1 });
  assert.equal((await client.resolve("yandex", "900003")).replacementId, 103);
  assert.equal((await client.resolve("yandex", "900004")).replacementId, 104);
  assert.equal((await client.resolve("yandex", "999998")).found, false);
  assert.deepEqual(Object.fromEntries(counts), { "900003": 1, "900004": 1, "999998": 1 }, "no cross-track cache poisoning");
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
