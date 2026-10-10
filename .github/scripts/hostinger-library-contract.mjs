import fs from "node:fs";
import { fileURLToPath } from "node:url";

const contracts = Object.freeze({
  validate: ["operation"],
  inspect: ["operation"],
  "add-track": ["operation", "track_id", "duration_ms", "confirm_owner"],
  "add-asset": ["operation", "duration_ms", "confirm_owner", "confirm_reviewed"],
  link: ["operation", "track_db_id", "asset_id", "confirm_owner"],
  approve: ["operation", "replacement_id", "confirm_owner", "confirm_reviewed"],
  activate: ["operation", "replacement_id", "expected_active_replacement_id", "confirm_owner", "confirm_activate"],
  disable: ["operation", "replacement_id", "expected_active_replacement_id", "confirm_owner", "confirm_disable"]
});
const positive = /^[1-9][0-9]{0,17}$/;
const track = /^[1-9][0-9]{0,23}$/;

export function validateLibraryRequest(data) {
  if (data === null || Array.isArray(data) || typeof data !== "object"
      || !Object.hasOwn(contracts, data.operation)) throw new Error("invalid_library_request");
  const keys = Object.keys(data).sort();
  if (keys.join("|") !== [...contracts[data.operation]].sort().join("|")) throw new Error("invalid_library_fields");
  const operation = data.operation;
  if (Object.hasOwn(data, "track_id") && (typeof data.track_id !== "string" || !track.test(data.track_id))) {
    throw new Error("invalid_track_id");
  }
  for (const field of ["track_db_id", "asset_id", "replacement_id"]) {
    if (Object.hasOwn(data, field) && (typeof data[field] !== "string" || !positive.test(data[field]))) {
      throw new Error("invalid_internal_id");
    }
  }
  if (Object.hasOwn(data, "expected_active_replacement_id") &&
      (typeof data.expected_active_replacement_id !== "string" ||
        !/^(0|[1-9][0-9]{0,17})$/.test(data.expected_active_replacement_id))) {
    throw new Error("invalid_expected_active");
  }
  if (Object.hasOwn(data, "duration_ms") &&
      (!Number.isSafeInteger(data.duration_ms) || data.duration_ms < 1000 || data.duration_ms > 86400000)) {
    throw new Error("invalid_duration_ms");
  }
  for (const key of ["confirm_owner", "confirm_reviewed", "confirm_activate", "confirm_disable"]) {
    if (Object.hasOwn(data, key) && data[key] !== true) throw new Error("explicit_confirmation_required");
  }
  return { operation, mutates: !["validate", "inspect"].includes(operation) };
}

export function readLibraryRequest(path) {
  const stats = fs.statSync(path);
  if (!stats.isFile() || stats.size > 2048 || stats.size < 2) throw new Error("invalid_request_file");
  return validateLibraryRequest(JSON.parse(fs.readFileSync(path, "utf8")));
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try {
    const result = readLibraryRequest(".github/deploy/hostinger-library-request.json");
    console.log("Stage 6 library request validated: " + result.operation +
      (result.mutates ? " (write operation; explicit owner authorization required)." : " (no DB/audio writes)."));
  } catch (_) {
    console.error("Invalid private library request; no Hostinger access performed.");
    process.exitCode = 2;
  }
}
