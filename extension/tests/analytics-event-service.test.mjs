import assert from "node:assert/strict";
import test from "node:test";
import { AnalyticsEventService } from "../dist/unpacked/api/analytics-event-service.js";

function fixture(enabled = true) {
  const stored = {}; const batches = []; let counter = 1; let fail = false;
  const api = { runtime: { getManifest: () => ({ version: "0.4.0" }) }, storage: { local: {
    get: async () => structuredClone(stored), set: async values => Object.assign(stored, structuredClone(values))
  } } };
  const client = { config: async () => ({ features: { analytics: enabled } }), events: async batch => {
    batches.push(structuredClone(batch)); if (fail) throw new Error("offline");
    return { results: batch.events.map(event => ({ event_id: event.event_id, status: "accepted" })) };
  } };
  const service = new AnalyticsEventService(api, async () => client, { uuid: () => `00000000-0000-4000-8000-${String(counter++).padStart(12, "0")}` });
  return { service, stored, batches, setFail: value => { fail = value; } };
}

test("analytics disabled creates no identity, queue or event request", async () => {
  const f = fixture(false); assert.equal(await f.service.enqueue("celikom_started"), false);
  assert.deepEqual(f.stored, {}); assert.equal(f.batches.length, 0);
});

test("analytics retries original event UUIDs and serializes concurrent events", async () => {
  const f = fixture(); f.setFail(true);
  await f.service.enqueue("replacement_started", { service: "yandex" });
  const first = f.stored.analyticsQueue[0].event_id; const installation = f.stored.analyticsInstallationId;
  f.setFail(false);
  await Promise.all([f.service.enqueue("manual_original"), f.service.enqueue("celikom_stopped")]);
  assert.equal(f.batches[1].events[0].event_id, first);
  assert.equal(f.batches[1].installation_id, installation);
  assert.equal(f.batches.length, 3); assert.deepEqual(f.stored.analyticsQueue, []);
  assert.deepEqual(Object.keys(f.batches[0].events[0]).sort(), ["event_id", "event_name", "occurred_at", "properties"]);
});

test("analytics rejects listening history, URLs and financial client claims", async () => {
  const f = fixture();
  for (const [name, properties] of [["payment_success", {}], ["replacement_started", { track_id: "7" }], ["fail_open", { url: "https://private" }], ["manual_original", { currentTime: 42 }], ["fail_open", { error_code: "arbitrary" }]]) {
    assert.equal(await f.service.enqueue(name, properties), false);
  }
  assert.deepEqual(f.stored, {}); assert.equal(f.batches.length, 0);
});
