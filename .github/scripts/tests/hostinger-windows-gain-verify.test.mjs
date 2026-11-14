import test from "node:test";
import assert from "node:assert/strict";
import { parseMetricsTsv, verifyGainReconciliation } from "../hostinger-windows-gain-verify.mjs";

const sourceSha = "a".repeat(64);
const renderSha = "b".repeat(64);
const commit = "c".repeat(40);

function fixture() {
  const beforeRow = {
    replacement_id: 37, track_id: "40371622", version: 4, gain_db: 11.5,
    source_sha256: sourceSha, duration_ms: 201000, source_size_bytes: 123456,
    already_staged: false, render_sha256: "", render_size_bytes: 0
  };
  const afterRow = {
    ...beforeRow, already_staged: true, render_sha256: renderSha, render_size_bytes: 100000
  };
  const metric = {
    replacement_id: 37, track_id: "40371622", version: 4, gain_db: 11.5,
    source_sha256: sourceSha, duration_ms: 201000, render_sha256: renderSha,
    render_size_bytes: 100000, status: "rendered", measured_rms_delta_db: 6.7,
    output_peak_db: 0
  };
  const liveCheck = {
    replacement_id: 37, track_id: "40371622", version: 4, gain_db: 11.5,
    source_sha256: sourceSha, sidecar_sha256: renderSha, duration_ms: 201000,
    source_size_bytes: 123456, gain_applied: true, http_status: 206,
    range_bytes: 65536, content_type: "audio/mpeg", etag_verified: true
  };
  return {
    before: { schema_020: true, count: 1, rows: [beforeRow] },
    after: { schema_020: true, count: 1, rows: [afterRow] },
    metrics: [metric],
    liveVerify: { session_entitled: true, count: 1, checks: [liveCheck] },
    commit
  };
}

test("W98 accepts exact before/after inventory, render and live Range identity", () => {
  const result = verifyGainReconciliation(fixture());
  assert.equal(result.inventory_identity_verified, true);
  assert.equal(result.post_stage_inventory_identity_verified, true);
  assert.equal(result.live_signed_http_range_checked, true);
  assert.equal(result.rows[0].replacement_id, 37);
});

test("W98 rejects a same-count replacement substitution after staging", () => {
  const data = fixture();
  data.after.rows[0].replacement_id = 38;
  assert.throws(() => verifyGainReconciliation(data), /W98_GAIN_REPLACEMENT_SET_CHANGED/);
});

test("W98 rejects source, version, gain, duration or size drift after staging", () => {
  for (const [field, value] of [
    ["source_sha256", "d".repeat(64)], ["version", 5], ["gain_db", 10],
    ["duration_ms", 202000], ["source_size_bytes", 123457]
  ]) {
    const data = fixture();
    data.after.rows[0][field] = value;
    assert.throws(() => verifyGainReconciliation(data), /W98_GAIN_SOURCE_IDENTITY_CHANGED_AFTER_STAGE/);
  }
});

test("W98 rejects a sidecar digest mismatch between inventory and render manifest", () => {
  const data = fixture();
  data.metrics[0].render_sha256 = "d".repeat(64);
  assert.throws(() => verifyGainReconciliation(data), /W98_GAIN_RENDER_MANIFEST_IDENTITY_MISMATCH/);
});

test("W98 rejects a live Range check bound to another track or sidecar", () => {
  for (const field of ["track_id", "source_sha256", "sidecar_sha256", "version", "duration_ms"]) {
    const data = fixture();
    data.liveVerify.checks[0][field] = field === "source_sha256" || field === "sidecar_sha256"
      ? "d".repeat(64) : field === "track_id" ? "999" : 99;
    assert.throws(() => verifyGainReconciliation(data), /W98_GAIN_LIVE_RANGE_IDENTITY_MISMATCH/);
  }
});

test("W98 rejects missing entitlement, non-206 and unverified ETag", () => {
  for (const mutate of [
    d => { d.liveVerify.session_entitled = false; },
    d => { d.liveVerify.checks[0].http_status = 200; },
    d => { d.liveVerify.checks[0].etag_verified = false; }
  ]) {
    const data = fixture();
    mutate(data);
    assert.throws(() => verifyGainReconciliation(data));
  }
});

test("W98 rejects duplicate replacement IDs in inventory or live checks", () => {
  const data = fixture();
  data.before.rows.push({ ...data.before.rows[0] });
  data.before.count = 2;
  assert.throws(() => verifyGainReconciliation(data), /W98_BEFORE_INVENTORY_ROW_INVALID/);

  const second = fixture();
  second.before.rows.push({ ...second.before.rows[0], replacement_id: 38, track_id: "40371623" });
  second.before.count = 2;
  second.after.rows.push({ ...second.after.rows[0], replacement_id: 38, track_id: "40371623" });
  second.after.count = 2;
  second.metrics.push({ ...second.metrics[0], replacement_id: 38, track_id: "40371623" });
  second.liveVerify.checks.push({ ...second.liveVerify.checks[0] });
  second.liveVerify.count = 2;
  assert.throws(() => verifyGainReconciliation(second), /W98_GAIN_LIVE_ID_DUPLICATE/);
});

test("W98 parses the exact 11-column private metrics format", () => {
  const line = [
    "37", "40371622", "4", "11.5", sourceSha, "201000",
    renderSha, "100000", "rendered", "6.70", "0.0"
  ].join("\t");
  const rows = parseMetricsTsv(line + "\n");
  assert.equal(rows.length, 1);
  assert.equal(rows[0].measured_rms_delta_db, 6.7);
  assert.equal(rows[0].output_peak_db, 0);
  assert.throws(() => parseMetricsTsv("37\tbad"), /W98_GAIN_METRICS_COLUMNS_INVALID/);
});
