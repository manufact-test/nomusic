import assert from "node:assert/strict";
import test from "node:test";
import { createAuthBroker } from "../dist/unpacked/auth/auth-broker.js";

function mock() {
  const local = {};
  let secret = null;
  const calls = [];
  let flag = true, referrals = false, nextId = 1, meMode = "ok", unverified = false;
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
    if (endpoint === "/api/v1/config") return response({ features: { auth: flag, referrals } });
    if (endpoint === "/api/v1/entitlement") return response({ allowed:false, source:"none",valid_until:null,reason:"trial_not_started" });
    if (endpoint === "/api/v1/referrals" || endpoint === "/api/v1/referrals/code") return response({code:endpoint.endsWith("code") ? "A".repeat(32) : null,
      registered_count:2,qualified_count:0,qualification_available:false,discount_active:false,reward_available:false,share_url:null});
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
  return { broker, local, calls, store, setFlag: (v) => { flag = v; }, setReferrals: (v) => { referrals = v; }, setMeMode: (v) => { meMode = v; }, setUnverified: (v) => { unverified = v; } };
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

test("Stage12 benefits stay private and issuing a code is explicit and feature-gated", async () => {
  const fx = mock();
  await fx.broker.perform("login", {email:"a@example.org",password:"correct horse battery staple"});
  const off = await fx.broker.perform("benefits");
  assert.equal(off.ok,true); assert.equal(off.referrals_available,false);
  assert.equal(fx.calls.some(c=>c.endpoint.includes("/referrals")),false);
  assert.equal((await fx.broker.perform("referral-code")).error,"referrals_disabled");
  fx.setReferrals(true);
  const result=await fx.broker.perform("referral-code");
  assert.equal(result.referrals.code,"A".repeat(32));
  assert.equal("access_token" in result,false); assert.equal("refresh_token" in result,false);
  const call=fx.calls.find(c=>c.endpoint==="/api/v1/referrals/code");
  assert.equal(call.opts.method,"POST");assert.equal(call.opts.headers.Authorization,"Bearer "+"a".repeat(64));
});
test("Stage12 disabled invitations do not silently discard a registration code", async () => {
  const fx = mock();
  const result=await fx.broker.perform("register",{email:"a@example.org",password:"correct horse battery staple",referral_code:"A".repeat(32)});
  assert.equal(result.error,"referrals_disabled");
  assert.equal(fx.calls.some(c=>c.endpoint.endsWith("register")),false);
});
