import { test } from "node:test";
import assert from "node:assert/strict";
import { createWindowsSourceBridge } from "./w4-source-resource-adapter.mjs";

const origin = "https://music.yandex.ru";
const url = "blob:https://music.yandex.ru/00000000-0000-4000-8000-000000000001";
const track = "50163040";
let clock;
const info = id => ({ trackId: String(id), codec: "aac", transport: "encraw",
  key: "synthetic-not-a-secret", encryptionKey: "fake", quality: "nq", urls: ["https://example.test/original"] });

function setup(kind = "v2", hooks = {}) {
  clock = 10_000_000;
  const gate = createWindowsSourceBridge({ origin, now: () => clock });
  class Resource {
    async getFileInfo(params) {
      if (hooks.waitForSingle) await hooks.waitForSingle();
      if (hooks.rejectSingle) throw Error("synthetic upstream unavailable");
      const value = hooks.errorSingle ? { ...info(params.trackId), error: "not_found" } : info(params.trackId);
      return kind === "v1" ? { downloadInfo: value } : { fileInfo: value };
    }
    async getFileInfoBatch(params) {
      const values = String(params.trackIds).split(",").map(info);
      return kind === "v1" ? { downloadInfos: values } : { fileInfos: values };
    }
  }
  const prototype = Resource.prototype;
  const original = { single: prototype.getFileInfo, batch: prototype.getFileInfoBatch };
  gate.install(prototype);
  gate.setEnabled(true);
  gate.setTrack(track);
  gate.registerPreparedAsset({ trackId: track, url, expiresAt: clock + 90_000,
    approved: true, entitled: true, durationMatched: true, audioValidated: true });
  return { gate, resource: new Resource(), prototype, original };
}

test("W4 single v1/v2: same exact track uses one raw MP3 source descriptor", async () => {
  for (const kind of ["v1", "v2"]) {
    const { gate, resource } = setup(kind);
    const response = await resource.getFileInfo({ trackId: track });
    const replacement = response.fileInfo || response.downloadInfo;
    assert.equal(replacement.trackId, track);
    assert.equal(replacement.url, url);
    assert.equal(replacement.codec, "mp3");
    assert.equal(replacement.transport, "raw");
    assert.equal(Object.hasOwn(replacement, "key"), false);
    assert.equal(Object.hasOwn(replacement, "encryptionKey"), false);
    gate.dispose();
  }
});

test("W4 batch: preserve request order and unmapped original tracks", async () => {
  const { gate, resource } = setup("v1");
  const response = await resource.getFileInfoBatch({ trackIds: "404,50163040,888" });
  assert.deepEqual(response.downloadInfos.map(item => item.trackId), ["404", track, "888"]);
  assert.equal(response.downloadInfos[0].transport, "encraw");
  assert.equal(response.downloadInfos[1].transport, "raw");
  assert.equal(response.downloadInfos[2].transport, "encraw");
  gate.dispose();
});

test("W4 rejects wrong track and batch prefetch cannot seize current identity", async () => {
  const { gate, resource } = setup();
  assert.equal((await resource.getFileInfo({ trackId: "101" })).fileInfo.transport, "encraw");
  const results = (await resource.getFileInfoBatch({ trackIds: "101,50163040" })).fileInfos;
  assert.equal(results[0].transport, "encraw");
  assert.equal(results[1].transport, "raw");
  assert.equal(gate.diagnostics().currentTrackKnown, true);
  gate.dispose();
});

test("W4 Next fences delayed in-flight original response", async () => {
  let release;
  const blocker = new Promise(resolve => { release = resolve; });
  const { gate, resource } = setup("v2", { waitForSingle: () => blocker });
  const stale = resource.getFileInfo({ trackId: track });
  gate.setTrack("99999");
  release();
  const result = await stale;
  assert.equal(result.fileInfo.transport, "encraw");
  assert.equal(gate.diagnostics().stale, 1);
  gate.dispose();
});

test("W4 abort leaves original response intact", async () => {
  const { gate, resource } = setup();
  const controller = new AbortController();
  controller.abort();
  assert.equal((await resource.getFileInfo({ trackId: track }, { signal: controller.signal })).fileInfo.transport, "encraw");
  gate.dispose();
});

test("W4 Original prevents later automatic substitution until next track", async () => {
  const { gate, resource } = setup();
  gate.original();
  assert.equal((await resource.getFileInfo({ trackId: track })).fileInfo.transport, "encraw");
  gate.setTrack("99999");
  gate.setTrack(track);
  assert.equal((await resource.getFileInfo({ trackId: track })).fileInfo.transport, "raw");
  gate.dispose();
});

test("W4 duplicate track notification must not override Original preference", async () => {
  const { gate, resource } = setup();
  gate.original();
  gate.setTrack(track); // duplicate event, not a new song
  assert.equal((await resource.getFileInfo({ trackId: track })).fileInfo.transport, "encraw");
  gate.dispose();
});

test("W4 duplicate hook install is rejected", () => {
  const { gate, prototype } = setup();
  assert.throws(() => gate.install(prototype), /already_installed/);
  gate.dispose();
});

test("W4 Stop rejects all pending and future requests", async () => {
  const { gate, resource } = setup();
  gate.stop();
  assert.equal((await resource.getFileInfo({ trackId: track })).fileInfo.transport, "encraw");
  assert.equal(gate.diagnostics().assetCount, 0);
  gate.dispose();
});

test("W4 expiry leaves original without retry loop", async () => {
  const { gate, resource } = setup();
  clock += 70_000; // Only 20 seconds left, below the expiry guard.
  assert.equal((await resource.getFileInfo({ trackId: track })).fileInfo.transport, "encraw");
  gate.dispose();
});

test("W4 unauthorized / mismatched / unsafe assets never admitted", () => {
  const { gate } = setup();
  const base = { trackId: track, url, expiresAt: clock + 90_000, approved: true,
    entitled: true, durationMatched: true, audioValidated: true };
  for (const patch of [
    { trackId: "not-an-ID" }, { url: "https://malicious.example/track.mp3" },
    { url: "blob:https://other.example/asset" }, { approved: false },
    { entitled: false }, { durationMatched: false }, { audioValidated: false },
    { expiresAt: clock + 1000 }, { expiresAt: clock + 400_000 }
  ]) assert.throws(() => gate.registerPreparedAsset({ ...base, ...patch }), /invalid_prepared_asset/);
  gate.dispose();
});

test("W4 original network failure remains a failure; no fabricated response", async () => {
  const { gate, resource } = setup("v2", { rejectSingle: true });
  await assert.rejects(resource.getFileInfo({ trackId: track }), /synthetic upstream unavailable/);
  gate.dispose();
});

test("W4 valid original error response is not transformed", async () => {
  const { gate, resource } = setup("v2", { errorSingle: true });
  const response = await resource.getFileInfo({ trackId: track });
  assert.equal(response.fileInfo.transport, "encraw");
  gate.dispose();
});

test("W4 unsupported prototype never partially modified", () => {
  const bridge = createWindowsSourceBridge({ origin });
  const resource = { getFileInfo: async () => info(track) };
  assert.throws(() => bridge.install(resource), /unsupported_resource_shape/);
  assert.equal(typeof resource.getFileInfo, "function");
  assert.equal(Object.hasOwn(resource, "getFileInfoBatch"), false);
  bridge.dispose();
});

test("W4 dispose removes only our installed wrappers", () => {
  const { gate, prototype, original } = setup();
  gate.dispose();
  assert.equal(prototype.getFileInfo, original.single);
  assert.equal(prototype.getFileInfoBatch, original.batch);
  assert.equal(gate.diagnostics().assetCount, 0);
});

test("W4 unhook preserves another owner's later change", () => {
  const { gate, prototype } = setup();
  const foreignHook = async () => ({ fileInfo: info(track) });
  prototype.getFileInfo = foreignHook;
  gate.dispose();
  assert.equal(prototype.getFileInfo, foreignHook);
});

test("W4 redacted diagnostics never export source URL, token, or file body", () => {
  const { gate } = setup();
  const report = JSON.stringify(gate.diagnostics());
  assert.equal(report.includes(url), false);
  assert.equal(report.includes("token"), false);
  gate.dispose();
});
