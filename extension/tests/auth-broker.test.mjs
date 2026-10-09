import assert from "node:assert/strict";
import test from "node:test";
import { createAuthBroker } from "../dist/unpacked/auth/auth-broker.js";

function mock() {
  const local = {};
  let secret = null;
  const calls = [];
  let flag = true, nextId = 1;
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
      nextId++;
      return response({ user: { id: 4, email: "a@example.org" }, access_token: "a".repeat(64),
        refresh_token: "b".repeat(64), token_type: "Bearer", expires_in: 900 }, endpoint.endsWith("register") ? 201 : 200);
    }
    if (endpoint.endsWith("refresh")) {
      return response({ user: { id: 4, email: "a@example.org" }, access_token: "c".repeat(64),
        refresh_token: "d".repeat(64), token_type: "Bearer", expires_in: 900 });
    }
    if (endpoint.endsWith("me")) return response({ user: { id: 4, email: "a@example.org" } });
    if (endpoint.endsWith("logout")) return response({ ok: true });
    if (endpoint.endsWith("sessions")) return response({ sessions: [{ id: 1, current: true }] });
    if (endpoint.endsWith("revoke") || endpoint.endsWith("activate")) return response({ ok: true });
    return response({ error: "invalid_request" }, 400);
  };
  const broker = createAuthBroker(api, { store, fetch, readConfig: async () => ({ baseUrl: "https://celikom.example" }) });
  return { broker, local, calls, store, setFlag: (v) => { flag = v; } };
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
