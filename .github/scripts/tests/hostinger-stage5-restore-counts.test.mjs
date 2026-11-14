import test from "node:test";
import assert from "node:assert/strict";
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
    "audio_assets\\t1498",
    "schema_migrations\\t20",
    "track_replacements\\t1493",
    "tracks\\t1493",
    "users\\t4",
    "windows_gain_variants\\t0",
    ""
  ].join("\\n"));
});

test("W98 restore accepts a pre-sidecar snapshot", () => {
  const parsed = parseSnapshotTableCountsJson(JSON.stringify(base));
  assert.equal(parsed.split("\\n").filter(Boolean).length, 4);
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
