import fs from "node:fs";

const SHA256 = /^[a-f0-9]{64}$/;
const COMMIT = /^[a-f0-9]{40}$/;
const fail = code => { throw new Error(code); };
const gainEqual = (a, b) => Number.isFinite(Number(a)) &&
  Number.isFinite(Number(b)) && Math.abs(Number(a) - Number(b)) <= 0.00001;

function inventoryMap(value, label) {
  if (!value || value.schema_020 !== true || !Array.isArray(value.rows) ||
      value.count !== value.rows.length || value.count < 1 || value.count > 50) {
    fail("W98_" + label + "_INVENTORY_SHAPE_INVALID");
  }
  const map = new Map();
  for (const row of value.rows) {
    const id = Number(row.replacement_id);
    if (!Number.isSafeInteger(id) || id < 1 || map.has(id) ||
        !/^[1-9][0-9]{0,23}$/.test(String(row.track_id)) ||
        !Number.isSafeInteger(Number(row.version)) || Number(row.version) < 1 ||
        !Number.isFinite(Number(row.gain_db)) || Number(row.gain_db) === 0 ||
        Math.abs(Number(row.gain_db)) > 12 ||
        !SHA256.test(String(row.source_sha256)) ||
        !Number.isSafeInteger(Number(row.duration_ms)) || Number(row.duration_ms) < 1000 ||
        !Number.isSafeInteger(Number(row.source_size_bytes)) || Number(row.source_size_bytes) < 1024 ||
        typeof row.already_staged !== "boolean") {
      fail("W98_" + label + "_INVENTORY_ROW_INVALID");
    }
    if (row.already_staged) {
      if (!SHA256.test(String(row.render_sha256)) ||
          !Number.isSafeInteger(Number(row.render_size_bytes)) || Number(row.render_size_bytes) < 1024) {
        fail("W98_" + label + "_SIDECAR_INVALID");
      }
    } else if (String(row.render_sha256 ?? "") !== "" || Number(row.render_size_bytes ?? 0) !== 0) {
      fail("W98_" + label + "_UNSTAGED_ROW_HAS_RENDER");
    }
    map.set(id, row);
  }
  return map;
}

export function parseMetricsTsv(source) {
  if (typeof source !== "string" || source.trim() === "") fail("W98_GAIN_METRICS_EMPTY");
  return source.replace(/(?:\r?\n)+$/, "").split(/\r?\n/).filter(Boolean).map(line => {
    const p = line.split("\t");
    if (p.length !== 11) fail("W98_GAIN_METRICS_COLUMNS_INVALID");
    const row = {
      replacement_id: Number(p[0]), track_id: p[1], version: Number(p[2]),
      gain_db: Number(p[3]), source_sha256: p[4], duration_ms: Number(p[5]),
      render_sha256: p[6], render_size_bytes: Number(p[7]), status: p[8],
      measured_rms_delta_db: p[9] === "" ? null : Number(p[9]),
      output_peak_db: p[10] === "" ? null : Number(p[10])
    };
    if (!Number.isSafeInteger(row.replacement_id) || row.replacement_id < 1 ||
        !/^[1-9][0-9]{0,23}$/.test(String(row.track_id)) ||
        !Number.isSafeInteger(row.version) || row.version < 1 ||
        !Number.isFinite(row.gain_db) || row.gain_db === 0 || Math.abs(row.gain_db) > 12 ||
        !SHA256.test(row.source_sha256) ||
        !Number.isSafeInteger(row.duration_ms) || row.duration_ms < 1000 ||
        !SHA256.test(row.render_sha256) ||
        !Number.isSafeInteger(row.render_size_bytes) || row.render_size_bytes < 1024 ||
        !["existing", "rendered"].includes(row.status)) fail("W98_GAIN_METRICS_ROW_INVALID");
    if (row.status === "rendered" &&
        (!Number.isFinite(row.measured_rms_delta_db) || !Number.isFinite(row.output_peak_db))) {
      fail("W98_GAIN_RENDER_MEASUREMENT_MISSING");
    }
    if (row.status === "existing" &&
        (row.measured_rms_delta_db !== null || row.output_peak_db !== null)) {
      fail("W98_GAIN_EXISTING_MEASUREMENT_INVALID");
    }
    return row;
  });
}

export function verifyGainReconciliation({ before, after, metrics, liveVerify, commit }) {
  if (!COMMIT.test(String(commit))) fail("W98_GAIN_COMMIT_ID_INVALID");
  const oldRows = inventoryMap(before, "BEFORE");
  const newRows = inventoryMap(after, "AFTER");
  if (oldRows.size !== newRows.size || !Array.isArray(metrics) || metrics.length !== oldRows.size ||
      !liveVerify || liveVerify.session_entitled !== true ||
      liveVerify.count !== oldRows.size || !Array.isArray(liveVerify.checks) ||
      liveVerify.checks.length !== oldRows.size) fail("W98_GAIN_RECONCILIATION_COUNT_MISMATCH");

  const metricMap = new Map();
  for (const row of metrics) {
    const id = Number(row.replacement_id);
    if (!Number.isSafeInteger(id) || metricMap.has(id)) fail("W98_GAIN_METRIC_ID_DUPLICATE");
    metricMap.set(id, row);
  }
  const liveMap = new Map();
  for (const row of liveVerify.checks) {
    const id = Number(row.replacement_id);
    if (!Number.isSafeInteger(id) || liveMap.has(id)) fail("W98_GAIN_LIVE_ID_DUPLICATE");
    liveMap.set(id, row);
  }

  for (const [id, old] of oldRows) {
    const current = newRows.get(id), metric = metricMap.get(id), live = liveMap.get(id);
    if (!current || !metric || !live) fail("W98_GAIN_REPLACEMENT_SET_CHANGED");
    const identity =
      String(old.track_id) === String(current.track_id) &&
      Number(old.version) === Number(current.version) &&
      gainEqual(old.gain_db, current.gain_db) &&
      String(old.source_sha256) === String(current.source_sha256) &&
      Number(old.duration_ms) === Number(current.duration_ms) &&
      Number(old.source_size_bytes) === Number(current.source_size_bytes);
    if (!identity) fail("W98_GAIN_SOURCE_IDENTITY_CHANGED_AFTER_STAGE");
    if (current.already_staged !== true || !SHA256.test(String(current.render_sha256)) ||
        Number(current.render_size_bytes) < 1024) fail("W98_GAIN_SIDECAR_NOT_PERSISTED");

    const status = old.already_staged ? "existing" : "rendered";
    if (metric.status !== status || String(metric.track_id) !== String(old.track_id) ||
        Number(metric.version) !== Number(old.version) || !gainEqual(metric.gain_db, old.gain_db) ||
        String(metric.source_sha256) !== String(old.source_sha256) ||
        Number(metric.duration_ms) !== Number(old.duration_ms) ||
        String(metric.render_sha256) !== String(current.render_sha256) ||
        Number(metric.render_size_bytes) !== Number(current.render_size_bytes)) {
      fail("W98_GAIN_RENDER_MANIFEST_IDENTITY_MISMATCH");
    }
    if (old.already_staged &&
        (String(old.render_sha256) !== String(current.render_sha256) ||
         Number(old.render_size_bytes) !== Number(current.render_size_bytes))) {
      fail("W98_GAIN_EXISTING_SIDECAR_CHANGED");
    }

    if (Number(live.replacement_id) !== id || String(live.track_id) !== String(old.track_id) ||
        Number(live.version) !== Number(old.version) || !gainEqual(live.gain_db, old.gain_db) ||
        String(live.source_sha256) !== String(old.source_sha256) ||
        String(live.sidecar_sha256) !== String(current.render_sha256) ||
        Number(live.duration_ms) !== Number(old.duration_ms) ||
        Number(live.source_size_bytes) !== Number(old.source_size_bytes) ||
        live.gain_applied !== true || live.http_status !== 206 || live.etag_verified !== true ||
        Number(live.range_bytes) < 1024 ||
        !String(live.content_type).toLowerCase().startsWith("audio/mpeg")) {
      fail("W98_GAIN_LIVE_RANGE_IDENTITY_MISMATCH");
    }
  }

  return {
    format: 1, commit, purpose: "windows-private-gain-sidecars",
    inventory_identity_verified: true, post_stage_inventory_identity_verified: true,
    live_entitlement_checked: true, live_signed_http_range_checked: true,
    checks: liveVerify.checks, rows: metrics
  };
}

function main() {
  const [beforePath, afterPath, metricsPath, livePath, commit, outputPath] = process.argv.slice(2);
  if (![beforePath, afterPath, metricsPath, livePath, commit, outputPath].every(Boolean)) {
    fail("W98_GAIN_VERIFY_ARGUMENTS_INVALID");
  }
  const before = JSON.parse(fs.readFileSync(beforePath, "utf8"));
  const after = JSON.parse(fs.readFileSync(afterPath, "utf8"));
  const metrics = parseMetricsTsv(fs.readFileSync(metricsPath, "utf8"));
  const liveVerify = JSON.parse(fs.readFileSync(livePath, "utf8"));
  const manifest = verifyGainReconciliation({ before, after, metrics, liveVerify, commit });
  fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2) + "\n", { mode: 0o600 });
  process.stdout.write("W98_GAIN_IDENTITY_RECONCILIATION_PASS count=" + manifest.rows.length + "\n");
}

if (process.argv[1]?.endsWith("hostinger-windows-gain-verify.mjs")) {
  try { main(); }
  catch (error) {
    const code = typeof error?.message === "string" && /^W98_[A-Z0-9_]+$/.test(error.message)
      ? error.message : "W98_GAIN_IDENTITY_RECONCILIATION_FAILED";
    process.stderr.write(code + "\n");
    process.exitCode = 2;
  }
}
