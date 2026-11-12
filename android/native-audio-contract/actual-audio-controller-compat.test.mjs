import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import {
  validateHeadResponse, validateRangeResponse, buildByteRangeHeaders
} from "./source-contract.mjs";

/**
 * Runs the exact unchanged production PHP controller, signed-token service,
 * inclusive ByteRange parser and response emitter with synthetic-only bytes.
 * No network / external service / auth data / production file touched.
 */
const here = dirname(fileURLToPath(import.meta.url));
function capture() {
  const raw = execFileSync("php", [resolve(here, "actual-audio-controller-fixture.php")],
    { encoding: "utf8", timeout: 12_000, maxBuffer: 32_768 });
  return JSON.parse(raw);
}
const body = Buffer.from("0123456789abcdef".repeat(256));
const sha = data => createHash("sha256").update(data).digest("hex");

test("real PHP AudioController emits exactly the expected HEAD 200 witness", () => {
  const w = capture();
  assert.equal(w.size, 4096);
  assert.equal(w.payloadSha256, sha(body));
  assert.deepEqual(w.real_server_classes_invoked,
    ["AudioController", "AudioTokenService", "ByteRange", "Response"]);
  assert.equal(w.head.status, 200);
  assert.equal(w.head.bodyBytes, 0);
  assert.equal(w.head.headers["Cache-Control"], "private, no-store");
  assert.equal(w.etag, `"${sha(body)}-3"`);
  const verified = validateHeadResponse({ status: w.head.status, headers: w.head.headers }, "audio/mpeg");
  assert.deepEqual(verified, { size: w.size, etag: w.etag, mimeType: "audio/mpeg" });
});

test("actual authenticated-by-HMAC PHP controller full/partial/EOF bytes validate exactly", () => {
  const w = capture();
  const head = validateHeadResponse({ status: w.head.status, headers: w.head.headers }, "audio/mpeg");
  const records = [
    [w.byteGet, 1024, 2047, 2047],
    [w.openEnd, 1024, null, 4095],
    [w.clippedEnd, 3000, 9999, 4095]
  ];
  for (const [response, start, requestedEnd, expectedEnd] of records) {
    const requested = buildByteRangeHeaders(start, requestedEnd, w.etag);
    assert.match(requested.Range, /^bytes=[0-9]+-[0-9]*$/);
    assert.equal(requested["If-Range"], w.etag);
    assert.equal(response.status, 206);
    const decision = validateRangeResponse(
      { status: response.status, headers: response.headers }, start, requestedEnd, head);
    assert.deepEqual(decision, {ok:true, start, end:expectedEnd, total:4096});
    const expected = body.subarray(start, expectedEnd + 1);
    assert.equal(response.bodyBytes, expected.length);
    assert.equal(response.bodySha256, sha(expected));
    assert.equal(response.headers["Cache-Control"], "private, no-store");
    assert.equal(response.headers["Content-Type"], "audio/mpeg");
  }
  assert.equal(w.fullGet.status, 200);
  assert.equal(w.fullGet.bodyBytes, 4096);
  assert.equal(w.fullGet.bodySha256, sha(body));
  assert.equal(validateRangeResponse(w.fullGet, 0, null, head).code, "RANGE_NOT_PARTIAL");
});

test("real PHP 416 and If-Range fallback cannot be misclassified as partial audio", () => {
  const w = capture();
  const head = validateHeadResponse({ status: w.head.status, headers: w.head.headers }, "audio/mpeg");
  assert.equal(w.invalidEnd.status, 416);
  assert.equal(w.invalidEnd.bodyBytes, 0);
  assert.equal(validateRangeResponse(
    {status:w.invalidEnd.status,headers:w.invalidEnd.headers},4096,null,head).code,
    "RANGE_UNSATISFIABLE");
  assert.equal(w.wrongIfRange.status, 200);
  assert.equal(w.wrongIfRange.bodyBytes,4096);
  assert.equal(validateRangeResponse(
    {status:w.wrongIfRange.status,headers:w.wrongIfRange.headers},1024,2047,head).code,
    "RANGE_NOT_PARTIAL");
});

test("actual PHP token denial and unverified session return no binary", () => {
  const w = capture();
  for (const denied of [w.wrongToken, w.unknownSession]) {
    assert.equal(denied.status, 403);
    assert.equal(denied.bodyBytes > 0, true);
    assert.equal(denied.headers["Content-Type"], "application/json; charset=utf-8");
    assert.equal(denied.headers["Cache-Control"], "no-store");
    assert.equal(validateRangeResponse(denied,1024,2047,
      {size:w.size,etag:w.etag}).ok,false);
  }
});
