import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseSnapshotTableCountsJson } from "../hostinger-stage5-restore-counts.mjs";

const base = {
  schema_migrations: 20,
  tracks: 1493,
  audio_assets: 1498,
  track_replacements: 1493
};

test("W98 restore count manifest is stable and sorted", () => {
  const parsed = parseSnapshotTableCountsJson(JSON.stringify({
    ...base,
    windows_gain_variants: 0,
    users: 4
  }));
  assert.equal(parsed, [
    "audio_assets\t1498",
    "schema_migrations\t20",
    "track_replacements\t1493",
    "tracks\t1493",
    "users\t4",
    "windows_gain_variants\t0",
    ""
  ].join("\n"));
});

test("W98 restore accepts a pre-sidecar snapshot", () => {
  const parsed = parseSnapshotTableCountsJson(JSON.stringify(base));
  assert.equal(parsed.split("\n").filter(Boolean).length, 4);
});

test("W98 restore rejects missing required tables", () => {
  assert.throws(() => parseSnapshotTableCountsJson(JSON.stringify({
    schema_migrations: 1, tracks: 1, audio_assets: 1
  })));
});

test("W98 restore rejects unsafe names and invalid row counts", () => {
  for (const invalid of [
    { ...base, "tracks; DROP TABLE users": 1 },
    { ...base, tracks: -1 },
    { ...base, tracks: 1.5 },
    { ...base, tracks: "1493" },
    { ...base, tracks: Number.MAX_SAFE_INTEGER + 1 }
  ]) {
    assert.throws(() => parseSnapshotTableCountsJson(JSON.stringify(invalid)));
  }
});

test("W98 restore rejects arrays, null and invalid JSON", () => {
  assert.throws(() => parseSnapshotTableCountsJson("[]"));
  assert.throws(() => parseSnapshotTableCountsJson("null"));
  assert.throws(() => parseSnapshotTableCountsJson("{"));
});


test("W98 live audit excludes only volatile session/auth/navigation row counts", () => {
  const remote = fs.readFileSync(
    path.join(path.dirname(fileURLToPath(import.meta.url)), "../hostinger-stage5-remote.php"),
    "utf8"
  );
  const match = remote.match(/\$volatileRowCountTables = \[(.*?)\];/s);
  assert.ok(match, "volatile row-count policy must be explicit");
  for (const table of [
    "admin_sessions",
    "user_sessions",
    "admin_login_attempts",
    "user_auth_attempts",
    "user_auth_events",
    "admin_navigation_seen"
  ]) {
    assert.ok(match[1].includes("'" + table + "'"), table + " must be treated as volatile");
  }
  for (const table of ["tracks", "audio_assets", "track_replacements"]) {
    assert.ok(!match[1].includes("'" + table + "'"), table + " must remain strictly checked");
  }
  assert.ok(remote.includes("if (in_array($table, $volatileRowCountTables, true)) continue;"));
  assert.ok(remote.includes("if ($currentCount < (int) $beforeCount)"));
  assert.ok(remote.includes("$currentCount > (int)$beforeCount + 2"));
  assert.ok(!remote.includes("if ($currentCount !== (int) $beforeCount)"));
});
