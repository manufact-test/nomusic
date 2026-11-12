import test from "node:test";
import assert from "node:assert/strict";
import {
  createAudioSourceContract, validateGrant, validateHeadResponse,
  buildByteRangeHeaders, validateRangeResponse
} from "./source-contract.mjs";

const NOW = 1_800_000_000_000;
const ORIGIN = "https://api.example.test/";
const TOKEN = "a".repeat(64);
const originalTrack = (trackId = "123", extras = {}) => ({
  trackId, durationMs: 180_000, albumId: "77", editionId: "studio-v1",
  paused: false, positionMs: 0, ...extras
});
function grant(trackId = "123", extras = {}) {
  const expiresAt = NOW + 600_000;
  return {
    trackId, approved: true, entitled: true, version: 3,
    albumId: "77", editionId: "studio-v1",
    mimeType: "audio/mpeg", durationMs: 180_000, expiresAt,
    audioUrl: ORIGIN + "api/v1/audio/42?token=" + TOKEN +
      "&expires=" + (expiresAt / 1000) + "&sid=17", ...extras
  };
}
function head(extras = {}) {
  return {
    status: 200,
    headers: {
      "content-type": "audio/mpeg", "content-length": "4500000",
      "accept-ranges": "bytes", etag: '"abc-3"', ...extras
    }
  };
}
function harness(overrides = {}) {
  const events = [];
  const opts = {
    origin: ORIGIN, now: () => NOW,
    resolve: async ({ trackId }) => grant(trackId),
    probeHead: async () => head(),
    onEvent: code => events.push(code), ...overrides
  };
  return { gate: createAudioSourceContract(opts), events };
}
async function prepared(overrides = {}) {
  const result = harness(overrides);
  result.gate.observeTrack(originalTrack());
  result.gate.enable();
  return result;
}

test("valid exact track/album/edition grant + HEAD selects only a source ticket", async () => {
  const { gate } = await prepared();
  const chosen = await gate.requestSource();
  assert.equal(chosen.action, "REPLACEMENT");
  assert.equal(chosen.trackId, "123");
  assert.equal(chosen.etag, '"abc-3"');
  assert.equal(chosen.byteLength, 4_500_000);
  assert.equal(gate.snapshot().state, "READY_NOT_APPLIED");
  assert.equal(gate.isCurrent(chosen), true);
  assert.equal(gate.commit(chosen, true), true);
  assert.equal(gate.snapshot().state, "SOURCE_SELECTED_NOT_AUDIBLE_VERIFIED");
});

test("exact track ID mandatory, no title/fuzzy matching or stale snapshot", async () => {
  const { gate } = await prepared();
  assert.equal(gate.observeTrack({ title: "Song", durationMs: 180_000 }), false);
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
  assert.equal(gate.snapshot().trackId, null);
});

test("wrong numeric track rejects an otherwise valid signed source", async () => {
  const { gate } = await prepared({ resolve: async () => grant("999") });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
});

test("wrong album and edition fail closed; unknown authority fails closed too", () => {
  assert.equal(validateGrant(grant("123", { albumId: "88" }), originalTrack(), ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { editionId: "live-v2" }), originalTrack(), ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { albumId: undefined }), originalTrack(), ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { editionId: undefined }), originalTrack(), ORIGIN, NOW), null);
});

test("actual backend without album/edition attestation must not silently claim a match", async () => {
  const { gate } = await prepared({ resolve: async () => grant("123", { albumId: null, editionId: null }) });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
});


test("unknown native album/edition never sends a source request and cannot match a generic grant", async () => {
  let resolved = 0;
  let headed = 0;
  const { gate } = harness({
    resolve: async () => { resolved++; return grant(); },
    probeHead: async () => { headed++; return head(); }
  });
  gate.enable();
  for (const extras of [
    { albumId: null, editionId: null },
    { albumId: null, editionId: "studio-v1" },
    { albumId: "77", editionId: null },
    { albumId: undefined, editionId: undefined }
  ]) {
    assert.equal(gate.observeTrack(originalTrack("123", extras)), true);
    const decision = await gate.requestSource();
    assert.equal(decision.action, "ORIGINAL");
    assert.equal(gate.isCurrent(decision), true);
  }
  assert.equal(resolved, 0, "Native identity absent: never try network resolve");
  assert.equal(headed, 0, "Native identity absent: never consume signed audio URL");
});

test("grant validation fails closed if either host identity or server attestation is absent", () => {
  for (const field of ["albumId", "editionId"]) {
    assert.equal(validateGrant(grant(), originalTrack("123", { [field]: null }),
      ORIGIN, NOW), null);
    assert.equal(validateGrant(grant("123", { [field]: null }), originalTrack(),
      ORIGIN, NOW), null);
  }
  assert.ok(validateGrant(grant(), originalTrack(), ORIGIN, NOW));
});

test("mismatched replacement duration is rejected", async () => {
  const { gate } = await prepared({ resolve: async () => grant("123", { durationMs: 210_000 }) });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
});

test("short native track cannot accept zero or negative replacement audio duration", () => {
  const shortTrack = originalTrack("123", { durationMs: 1000 });
  assert.equal(validateGrant(grant("123", { durationMs: 0 }), shortTrack, ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { durationMs: -1 }), shortTrack, ORIGIN, NOW), null);
  assert.ok(validateGrant(grant("123", { durationMs: 1 }), shortTrack, ORIGIN, NOW));
});

test("unknown edition IDs must be exact strings, never implicit object or number coercion", async () => {
  let coercionCalls = 0;
  const coercible = { toString() { coercionCalls++; return "studio-v1"; } };
  const { gate } = await prepared();
  for (const bad of [1, false, coercible, "\u0000studio", "studio\n", "x".repeat(129)]) {
    assert.equal(gate.observeTrack(originalTrack("123", { editionId: bad })), false);
    assert.equal((await gate.requestSource()).action, "ORIGINAL");
  }
  assert.equal(coercionCalls, 0, "Do not execute attacker-provided toString()");
  assert.equal(gate.observeTrack(originalTrack("123", { editionId: "альбом:студия" })), true);
  assert.equal((await gate.requestSource()).action, "ORIGINAL", "Unknown edition must not be fabricated as a valid grant");
});

test("duration tolerance exact boundary accepted", () => {
  assert.ok(validateGrant(grant("123", { durationMs: 182_000 }), originalTrack(), ORIGIN, NOW));
  assert.equal(validateGrant(grant("123", { durationMs: 182_001 }), originalTrack(), ORIGIN, NOW), null);
});

test("missing replacement, denied entitlement and unapproved replacement go ORIGINAL", async () => {
  for (const value of [null, grant("123", { entitled: false }), grant("123", { approved: false })]) {
    const { gate } = await prepared({ resolve: async () => value });
    assert.equal((await gate.requestSource()).action, "ORIGINAL");
  }
});

test("untrusted signed URL origin/credentials/path/fragment never accepted", () => {
  for (const audioUrl of [
    "https://evil.example.test/api/v1/audio/42?token=" + TOKEN + "&expires=" + (NOW / 1000 + 600) + "&sid=17",
    "http://api.example.test/api/v1/audio/42?token=" + TOKEN + "&expires=" + (NOW / 1000 + 600) + "&sid=17",
    "https://user:pass@api.example.test/api/v1/audio/42?token=" + TOKEN + "&expires=" + (NOW / 1000 + 600) + "&sid=17",
    ORIGIN + "api/v1/other/42?token=" + TOKEN + "&expires=" + (NOW / 1000 + 600) + "&sid=17",
    grant().audioUrl + "#fragment"
  ]) assert.equal(validateGrant(grant("123", { audioUrl }), originalTrack(), ORIGIN, NOW), null);
});

test("duplicate, extra or missing signed parameters, missing sid fail closed", () => {
  const base = grant().audioUrl;
  for (const audioUrl of [base + "&sid=17", base + "&x=1", base.replace("&sid=17", ""),
    base.replace("token=" + TOKEN, "token=no")]) {
    assert.equal(validateGrant(grant("123", { audioUrl }), originalTrack(), ORIGIN, NOW), null);
  }
});

test("expired, near-expired, overlong, stale token timestamp and version mismatch fail", () => {
  const t = originalTrack();
  const expired = NOW + 10_000;
  const farFuture = NOW + 60 * 60_000;
  assert.equal(validateGrant(grant("123", { expiresAt: expired }), t, ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { expiresAt: farFuture }), t, ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { version: 2 }), originalTrack("123", { replacementVersion: 3 }), ORIGIN, NOW), null);
  assert.equal(validateGrant(grant("123", { expiresAt: NOW + 610_000 }), t, ORIGIN, NOW), null);
});

test("HEAD must be 200 full metadata and valid immutable identity", () => {
  assert.deepEqual(validateHeadResponse(head(), "audio/mpeg"), { size: 4_500_000, etag: '"abc-3"', mimeType: "audio/mpeg" });
  for (const invalid of [
    { ...head(), status: 206 }, head({ "accept-ranges": "none" }),
    head({ "content-length": "0" }), head({ etag: "weak" }),
    head({ "content-type": "text/html" })
  ]) assert.equal(validateHeadResponse(invalid, "audio/mpeg"), null);
});

test("invalid HEAD or unavailable source falls back without player/host writes", async () => {
  let called = 0;
  const { gate } = await prepared({ probeHead: async () => { called++; return { ...head(), status: 403 }; } });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
  assert.equal(called, 1);
});

test("Range headers represent bytes (never guess from playback milliseconds)", () => {
  assert.deepEqual(buildByteRangeHeaders(1024, 2047, '"abc-3"'), {
    Range: "bytes=1024-2047", "If-Range": '"abc-3"'
  });
  assert.deepEqual(buildByteRangeHeaders(0), { Range: "bytes=0-" });
  assert.throws(() => buildByteRangeHeaders(100, 10), /INVALID_BYTE_RANGE/);
  assert.throws(() => buildByteRangeHeaders(-1), /INVALID_BYTE_RANGE/);
});

test("GET 206 matching range / length / ETag is accepted", () => {
  const response = { status: 206, headers: {
    "content-range": "bytes 2048-4095/4500000",
    "content-length": "2048", etag: '"abc-3"', "content-type": "audio/mpeg"
  }};
  assert.deepEqual(validateRangeResponse(response, 2048, 4095, {
    size: 4_500_000, etag: '"abc-3"', mimeType: "audio/mpeg"
  }), { ok: true, start: 2048, end: 4095, total: 4_500_000 });
  assert.equal(validateRangeResponse(response, 1024).ok, false);
  assert.equal(validateRangeResponse(response, 2048, 3072).ok, false);
  assert.equal(validateRangeResponse(response, 2048, 4095, {size: 4_500_000, etag: '"old"'}).ok, false);
});



test("206 MIME must match the publisher-agnostic trusted HEAD witness", () => {
  const witness = validateHeadResponse(head(), "audio/mpeg");
  assert.equal(witness.mimeType, "audio/mpeg");
  const correct = {status:206,headers:{
    "content-range":"bytes 0-9/4500000","content-length":"10",
    "etag":witness.etag,"content-type":"audio/mpeg"
  }};
  assert.equal(validateRangeResponse(correct,0,9,witness).ok,true);
  for (const mime of ["audio/mp4","application/json","text/plain",null]) {
    const bad={...correct,headers:{...correct.headers,
      ...(mime===null ? {} : {"content-type":mime})}};
    if (mime===null) delete bad.headers["content-type"];
    assert.equal(validateRangeResponse(bad,0,9,witness).code,"RANGE_MISMATCH");
  }
});

test("PHP ByteRange must deliver the exact requested inclusive end, never a shortened 206", () => {
  const witnessed = { size: 10_000, etag: '"exact-v1"', mimeType: "audio/mpeg" };
  function partial(first, last, total = witnessed.size, length = last - first + 1) {
    return { status: 206, headers: {
      "content-range": `bytes ${first}-${last}/${total}`,
      "content-length": String(length), etag: witnessed.etag,
      "content-type": witnessed.mimeType
    }};
  }
  // PHP ByteRange::parse(start-end) always caps end to EOF.
  assert.deepEqual(validateRangeResponse(partial(1024, 2047), 1024, 2047, witnessed),
    { ok: true, start: 1024, end: 2047, total: 10_000 });
  assert.deepEqual(validateRangeResponse(partial(9000, 9999), 9000, 12000, witnessed),
    { ok: true, start: 9000, end: 9999, total: 10_000 });
  // Open end means all the remaining bytes of the verified object.
  assert.deepEqual(validateRangeResponse(partial(9000, 9999), 9000, null, witnessed),
    { ok: true, start: 9000, end: 9999, total: 10_000 });
  // These were previously incorrectly accepted because only <= was checked.
  assert.equal(validateRangeResponse(partial(1024, 1500), 1024, 2047, witnessed).code,
    "RANGE_MISMATCH");
  assert.equal(validateRangeResponse(partial(9000, 9500), 9000, null, witnessed).code,
    "RANGE_MISMATCH");
});

test("PHP HEAD and Range reject noncanonical Content-Length from wrong intermediaries", () => {
  const expected = { size: 4_500_000, etag: '"abc-3"', mimeType: "audio/mpeg" };
  const partial = { status: 206, headers: {
    "content-range": "bytes 2048-4095/4500000",
    "content-length": "2048", etag: expected.etag, "content-type": expected.mimeType
  }};
  assert.equal(validateRangeResponse(partial, 2048, 4095, expected).ok, true);
  for (const malformed of ["2.048e3", "0x800", " 2048", "2048 ", "002048", "+2048"]) {
    assert.equal(validateRangeResponse({
      ...partial, headers: { ...partial.headers, "content-length": malformed }
    }, 2048, 4095, expected).ok, false, malformed);
  }
  for (const malformed of ["4.5e6", "0x44aa20", " 4500000", "04500000", "+4500000"]) {
    assert.equal(validateHeadResponse(head({"content-length":malformed}), "audio/mpeg"),
      null, malformed);
  }
});

test("416 returns honest unsatisfiable, 200 range fallback not falsely accepted", () => {
  const expected = { size: 4_500_000, etag: '"abc-3"', mimeType: "audio/mpeg" };
  assert.equal(validateRangeResponse({
    status: 416, headers: {"content-range": "bytes */4500000"}
  }, 4_500_000, null, expected).code, "RANGE_UNSATISFIABLE");
  assert.equal(validateRangeResponse(head(), 0, null, expected).code, "RANGE_NOT_PARTIAL");
  assert.equal(validateRangeResponse({
    status: 416, headers: {"content-range": "bytes */3500000"}
  }, 4_500_000, null, expected).code, "RANGE_MISMATCH");
  assert.equal(validateRangeResponse({
    status: 416, headers: {"content-range": "bytes */4500000"}
  }, 1024, null, expected).code, "RANGE_MISMATCH");
});

test("206 and 416 reject missing or untrusted HEAD witness", () => {
  const response = { status: 206, headers: {
    "content-range": "bytes 2048-4095/4500000",
    "content-length": "2048", etag: '"abc-3"'
  }};
  for (const witness of [null, undefined, {}, {size: 4500000},
                         {size: 4500000, etag: 'W/"weak"'},
                         {size: 0, etag: '"abc-3"'}]) {
    assert.equal(validateRangeResponse(response, 2048, 4095, witness).code,
                 "HEAD_WITNESS_REQUIRED");
  }
  assert.equal(validateRangeResponse({
    status: 416, headers: {"content-range": "bytes */4500000"}
  }, 4_500_000).code, "HEAD_WITNESS_REQUIRED");
});

test("Next cancels late old-track resolve; stale response cannot commit", async () => {
  let release;
  const { gate } = await prepared({ resolve: () => new Promise(done => { release = done; }) });
  const old = gate.requestSource();
  await Promise.resolve();
  gate.next(originalTrack("456"));
  if (release) release(grant("123"));
  const result = await old;
  assert.equal(result.action, "IGNORE");
  assert.equal(gate.snapshot().trackId, "456");
  assert.equal(gate.commit(result, true), false);
});

test("MyWave/random unknown next is ORIGINAL while asynchronous matching is pending", async () => {
  let release;
  const { gate } = await prepared({ resolve: () => new Promise(done => { release = done; }) });
  const pending = gate.requestSource();
  await Promise.resolve();
  gate.myWave({ title: "no id", durationMs: 180_000 });
  if (release) release(grant());
  assert.equal((await pending).action, "IGNORE");
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
});

test("pause/seek/resume preserve the native host timeline; no second clock", async () => {
  const { gate } = await prepared();
  gate.pause();
  gate.seek(80_000);
  const result = await gate.requestSource();
  assert.equal(result.paused, true);
  assert.equal(result.positionMs, 80_000);
  gate.resume();
  gate.seek(130_000);
  assert.equal(gate.snapshot().paused, false);
  assert.equal(gate.snapshot().positionMs, 130_000);
  // Transport changes do not invalidate a source; native host still owns seek.
  assert.equal(gate.isCurrent(result), true);
});

test("Stop reverts to original immediately; re-enable reevaluates same track", async () => {
  const { gate } = await prepared();
  const replacement = await gate.requestSource();
  gate.disable();
  assert.equal(gate.isCurrent(replacement), false);
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
  assert.equal(gate.snapshot().state, "OFF");
  gate.enable();
  assert.equal((await gate.requestSource()).action, "REPLACEMENT");
});

test("repeated Start and Stop are idempotent, force-original remains explicit", async () => {
  const { gate } = await prepared();
  const first = gate.snapshot().generation;
  gate.enable();
  assert.equal(gate.snapshot().generation, first);
  gate.preferOriginal();
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
  gate.enable();
  assert.equal((await gate.requestSource()).action, "REPLACEMENT");
  gate.disable();
  const off = gate.snapshot().generation;
  gate.disable();
  assert.equal(gate.snapshot().generation, off);
});

test("offline resolver exception and HEAD exception never interrupt original playback", async () => {
  for (const options of [
    { resolve: async () => { throw new Error("network secret"); } },
    { probeHead: async () => { throw new Error("transport"); } }
  ]) {
    const { gate } = await prepared(options);
    assert.equal((await gate.requestSource()).action, "ORIGINAL");
  }
});

test("time budget fail-open with never-finishing resolver", async () => {
  const { gate } = await prepared({
    deadlineMs: 20, resolve: async () => new Promise(() => {})
  });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
  assert.equal(gate.snapshot().state, "ORIGINAL");
});

test("grant expires during HEAD: discard even if it was valid at resolve time", async () => {
  let clock = NOW;
  const { gate } = await prepared({
    now: () => clock,
    probeHead: async () => { clock = NOW + 580_001; return head(); }
  });
  assert.equal((await gate.requestSource()).action, "ORIGINAL");
});

test("end/dispose invalidate outstanding requests, prevent reactivation", async () => {
  const { gate } = await prepared();
  const selected = await gate.requestSource();
  gate.ended();
  assert.equal(gate.isCurrent(selected), false);
  gate.dispose();
  gate.enable();
  assert.equal((await gate.requestSource()).action, "IGNORE");
  assert.equal(gate.snapshot().state, "OFF");
});

test("diagnostic codes contain no signed URL, token, ID or account data", async () => {
  const { gate, events } = await prepared();
  await gate.requestSource();
  gate.disable();
  const body = JSON.stringify(events);
  assert.ok(!body.includes(TOKEN));
  assert.ok(!body.includes("api/v1/audio"));
  assert.ok(!body.includes("123"));
  assert.ok(events.includes("SOURCE_VALIDATED_NOT_AUDIBLE"));
});

test("unsupported native host failure does not imply audible audio", async () => {
  const { gate } = await prepared();
  const result = await gate.requestSource();
  assert.equal(gate.commit(result, false), false);
  assert.equal(gate.snapshot().state, "ORIGINAL");
});

test("late HEAD after Next is ignored even when probe ignores AbortSignal", async () => {
  let release;
  const { gate } = await prepared({ probeHead: () => new Promise(done => { release = done; }) });
  const old = gate.requestSource();
  await Promise.resolve();
  await Promise.resolve();
  gate.next(originalTrack("456"));
  if (release) release(head());
  assert.equal((await old).action, "IGNORE");
});

test("forged/replayed ticket is rejected; valid ticket is one-shot", async () => {
  const { gate } = await prepared();
  const ticket = await gate.requestSource();
  assert.equal(ticket.action, "REPLACEMENT");
  const forged = { ...ticket };
  assert.equal(gate.isCurrent(forged), false);
  assert.equal(gate.commit(forged, true), false);
  assert.equal(gate.commit(ticket, true), true);
  assert.equal(gate.isCurrent(ticket), false);
  assert.equal(gate.commit(ticket, true), false);
  assert.equal(gate.snapshot().state, "SOURCE_SELECTED_NOT_AUDIBLE_VERIFIED");
});

test("ticket cannot cross source-contract instances even with identical state", async () => {
  const first = await prepared();
  const second = await prepared();
  const ticket = await first.gate.requestSource();
  await second.gate.requestSource();
  assert.equal(second.gate.isCurrent(ticket), false);
  assert.equal(second.gate.commit(ticket, true), false);
});

test("late cancellation and failed host application consume or revoke ticket", async () => {
  const { gate } = await prepared();
  const failed = await gate.requestSource();
  assert.equal(gate.commit(failed, false), false);
  assert.equal(gate.isCurrent(failed), false);
  assert.equal(gate.commit(failed, true), false);
  const pending = await gate.requestSource();
  gate.next(originalTrack("456"));
  assert.equal(gate.commit(pending, true), false);
  assert.equal(gate.isCurrent(pending), false);
});
