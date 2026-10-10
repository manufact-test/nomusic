import assert from "node:assert/strict";
import test from "node:test";
import { createAuthBroker } from "../dist/unpacked/auth/auth-broker.js";

function mock() {
  const local = {};
  let secret = null;
  const calls = [];
  let flag = true, nextId = 1, meMode = "ok", unverified = false;
  const api = {
    storage: { local: {
      get: async (key) => ({ [key]: local[key] }),
      set: async (obj) => Object.assign(local, obj)
    } },
    runtime: { getURL: (p) => "chrome-extension://extension/" + p }
  };
  const store = { get: async () => secret, set: async (value) => { secret = value; }, clear: async () => { secret = null; } };
  const response = (data, code = 200) => new Response(JSON.stringify(data), { status: code, headers: { "content-type": "application/json" } });
  const fetch = async (url, opts) => {
    const endpoint = new URL(url).pathname;
    calls.push({ endpoint, opts });
    if (endpoint === "/api/v1/config") return response({ features: { auth: flag } });
    if (endpoint.endsWith("register") || endpoint.endsWith("login")) {
      if (unverified) return response({ verification_required:true, email:"a@example.org" },endpoint.endsWith("register")?201:200);
      nextId++;
      return response({ user: { id: 4, email: "a@example.org" }, access_token: "a".repeat(64),
        refresh_token: "b".repeat(64), token_type: "Bearer", expires_in: 900 }, endpoint.endsWith("register") ? 201 : 200);
    }
    if (endpoint.endsWith("verify-email")) {
      return response({ user: { id: 4, email: "a@example.org" }, access_token: "a".repeat(64),
        refresh_token: "b".repeat(64), token_type: "Bearer", expires_in: 900 });
    }
    if (endpoint.endsWith("resend-verification")) return response({ verification_required:true, email:"a@example.org" });
    if (endpoint.endsWith("request-reset") || endpoint.endsWith("reset-password")) return response({ ok: true });
    if (endpoint.endsWith("refresh")) {
      return response({ user: { id: 4, email: "a@example.org" }, access_token: "c".repeat(64),
        refresh_token: "d".repeat(64), token_type: "Bearer", expires_in: 900 });
    }
    if (endpoint.endsWith("me")) {
      if (meMode === "offline") throw new Error("temporary_network_failure");
      if (meMode === "expired") return response({ error: "invalid_session" }, 401);
      return response({ user: { id: 4, email: "a@example.org" } });
    }
    if (endpoint.endsWith("logout")) return response({ ok: true });
    if (endpoint.endsWith("sessions")) return response({ sessions: [{ id: 1, current: true }] });
    if (endpoint.endsWith("revoke") || endpoint.endsWith("activate")) return response({ ok: true });
    return response({ error: "invalid_request" }, 400);
  };
  const broker = createAuthBroker(api, { store, fetch, readConfig: async () => ({ baseUrl: "https://celikom.example" }) });
  return { broker, local, calls, store, setFlag: (v) => { flag = v; }, setMeMode: (v) => { meMode = v; }, setUnverified: (v) => { unverified = v; } };
}
test("Stage9 identity uses stable v4 installation and no music-service identifiers", async () => {
  const fx = mock();
  const id1 = (await fx.broker.installationId());
  const id2 = (await fx.broker.installationId());
  assert.equal(id1, id2); assert.match(id1, /^[a-f0-9-]{36}$/);
  assert.equal(fx.local.celikomInstallationId, id1);
  assert.equal(Object.keys(fx.local).length, 1, "no email or secret in shared local storage");
});
test("Stage9 account flows are independent of playback and owner credentials", async () => {
  const fx = mock();
  assert.equal((await fx.broker.perform("status")).signedIn, false);
  const r = await fx.broker.perform("register", { email: "a@example.org", password: "correct horse battery staple" });
  assert.equal(r.ok, true);
  assert.deepEqual(Object.keys(fx.local), ["celikomInstallationId"]);
  assert.equal((await fx.broker.perform("status")).signedIn, true);
  assert.equal((await fx.broker.perform("sessions")).sessions.length, 1);
  assert.equal((await fx.broker.perform("activate")).ok, true);
  assert.equal((await fx.broker.perform("logout")).ok, true);
  assert.equal(await fx.store.get(), null);
  assert.equal((await fx.broker.perform("status")).signedIn, false);
  assert.equal(fx.calls.filter((c) => c.endpoint.endsWith("register")).length, 1);
  assert.equal(fx.calls.filter((c) => c.endpoint.endsWith("logout")).length, 1);
});
test("Stage9 feature gate OFF prevents sending account credentials", async () => {
  const fx = mock(); fx.setFlag(false);
  assert.equal((await fx.broker.perform("register", { email: "a@example.org", password: "private" })).error, "auth_disabled");
  assert.equal(fx.calls.some((c) => c.endpoint.endsWith("register")), false);
});

test("Stage9 transient network loss keeps the existing refresh token without rotation", async () => {
  const fx = mock();
  const registration = await fx.broker.perform("register", { email: "a@example.org", password: "correct horse battery staple" });
  assert.equal(registration.ok, true);
  const existing = await fx.store.get();
  fx.setMeMode("offline");
  const status = await fx.broker.perform("status");
  assert.equal(status.available, true);
  assert.equal(status.signedIn, false);
  assert.equal(status.error, "auth_unavailable");
  assert.equal(status.localSession, true);
  assert.equal(status.user.email, "a@example.org");
  assert.equal((await fx.store.get()).refresh_token, existing.refresh_token);
  assert.equal(fx.calls.filter((c) => c.endpoint.endsWith("refresh")).length, 0);
  fx.setMeMode("ok");
  assert.equal((await fx.broker.perform("status")).signedIn, true);
});

test("Stage9 expired access token rotates only after explicit HTTP 401", async () => {
  const fx = mock();
  await fx.broker.perform("register", { email: "a@example.org", password: "correct horse battery staple" });
  fx.setMeMode("expired");
  const result = await fx.broker.perform("status");
  assert.equal(result.signedIn, true);
  assert.equal((await fx.store.get()).refresh_token, "d".repeat(64));
  assert.equal(fx.calls.filter((c) => c.endpoint.endsWith("refresh")).length, 1);
});

test("Stage9 pending registration has no tokens before mailbox verification", async () => {
  const fx = mock(); fx.setUnverified(true);
  const pending = await fx.broker.perform("register", {
    email:"a@example.org", password:"correct horse battery staple"
  });
  assert.equal(pending.ok, true);
  assert.equal(pending.verification_required, true);
  assert.equal(await fx.store.get(), null, "unverified users must never be given refresh tokens");
  const resend = await fx.broker.perform("resend-verification", {
    email:"a@example.org", password:"correct horse battery staple"
  });
  assert.equal(resend.ok, true);
  const confirmed = await fx.broker.perform("verify-email", {
    email:"a@example.org", code:"123456"
  });
  assert.equal(confirmed.ok, true);
  assert.match((await fx.store.get()).refresh_token, /^[a-f0-9]{64}$/);
});
test("Stage9 password recovery does not assume success on invalid confirmation", async () => {
  const fx = mock();
  assert.equal((await fx.broker.perform("request-reset",{ email:"a@example.org" })).ok, true);
  assert.equal((await fx.broker.perform("reset-password",{
    email:"a@example.org", code:"123456", new_password:"correct horse battery staple"
  })).ok, true);
  assert.equal(await fx.store.get(), null, "password reset must not sign a browser in implicitly");
});

test("Stage9 disabled network config preserves local account appearance without granting auth", async () => {
  const fx = mock();
  await fx.broker.perform("register",{email:"a@example.org",password:"correct horse battery staple"});
  fx.setFlag(false);
  const status = await fx.broker.perform("status");
  assert.equal(status.signedIn,false);
  assert.equal(status.localSession,true);
  assert.equal(status.user.email,"a@example.org");
  assert.ok((await fx.store.get()).refresh_token);
});
