import assert from "node:assert/strict";
import test from "node:test";
import { createAuthBroker } from "../dist/unpacked/auth/auth-broker.js";

function mock() {
  const local = {};
  let secret = null;
  const calls = [];
  let flag = true, referrals = false, rewards = false, nextId = 1, meMode = "ok", unverified = false;
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
    if (endpoint === "/api/v1/config") return response({ features: { auth: flag, referrals, rewards } });
    if (endpoint === "/api/v1/rewards") return response({ earned_contributions: 7, earned_discount_percent: 21,
      available_discount_percent: 20, carried_discount_percent: 1, monthly_cap_percent: 20,
      next_available_from: "2026-11-01", expiry_starts: "payment", application_available: false, discount_active: false });
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
  return { broker, local, calls, store, setFlag: (v) => { flag = v; }, setReferrals: (v) => { referrals = v; }, setRewards: (v) => { rewards = v; }, setMeMode: (v) => { meMode = v; }, setUnverified: (v) => { unverified = v; } };
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

test("popup entitlement preview is account-scoped presentation without a network request and clears on logout", async () => {
  const m = mock();
  await m.broker.perform("login", { email: "a@example.org", password: "longpassword123" });
  await m.broker.perform("entitlement");
  const count = m.calls.length;
  const preview = await m.broker.perform("access-preview");
  assert.equal(preview.entitlement.reason, "trial_not_started");
  assert.equal(m.calls.length, count);
  assert.equal(JSON.stringify(preview).includes("access_token"), false);
  await m.broker.perform("logout");
  assert.equal((await m.broker.perform("access-preview")).entitlement, null);
});

test("automatic contribution benefits use own bearer and do not need invitation feature", async () => {
  const fx = mock();
  await fx.broker.perform("login", { email: "a@example.org", password: "longpassword123" });
  fx.setRewards(true);
  const result = await fx.broker.perform("benefits");
  assert.equal(result.ok, true); assert.equal(result.referrals_available, false); assert.equal(result.rewards_available, true);
  assert.equal(result.rewards.earned_discount_percent, 21); assert.equal(result.rewards.carried_discount_percent, 1);
  const call = fx.calls.find((c) => c.endpoint === "/api/v1/rewards");
  assert.equal(call.opts.headers.Authorization, "Bearer " + "a".repeat(64));
  assert.equal(JSON.stringify(result).includes("access_token"), false);
  await fx.broker.perform("logout");
  assert.equal((await fx.broker.perform("benefits")).ok, false);
});

test('account presence preview is immediate, credential-free and cannot authorize playback',async()=>{
 const fx=mock();
 const empty=await fx.broker.perform('account-preview');
 assert.equal(empty.localSession,false);assert.equal(fx.calls.length,0,'no config or network request before missing-account feedback');
 await fx.broker.perform('login',{email:'a@example.org',password:'longpassword123'});
 const calls=fx.calls.length,preview=await fx.broker.perform('account-preview');
 assert.equal(preview.localSession,true);assert.equal(fx.calls.length,calls);
 assert.deepEqual(Object.keys(preview).sort(),['localSession','ok']);
});


test('security: oversized chunked auth response is cancelled before buffering the rest',async()=>{
 let cancelled=false,reads=0,secret=null;
 const api={storage:{local:{get:async()=>({}),set:async()=>{}}},runtime:{getURL:p=>p}};
 const broker=createAuthBroker(api,{readConfig:async()=>({baseUrl:'https://celikom.example'}),
  store:{get:async()=>secret,set:async value=>{secret=value},clear:async()=>{secret=null}},
  fetch:async()=>new Response(new ReadableStream({
   pull(controller){reads++;controller.enqueue(new Uint8Array(8192));},
   cancel(){cancelled=true;}
  },{highWaterMark:0}),{headers:{'content-type':'application/json'}})});
 const result=await broker.perform('login',{email:'a@example.org',password:'abcdefghijk'});
 assert.equal(result.ok,false);assert.equal(cancelled,true);assert.equal(reads,3);assert.equal(secret,null);
});
