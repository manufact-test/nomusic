import test from "node:test";
import assert from "node:assert/strict";
import { validateLibraryRequest } from "../hostinger-library-contract.mjs";

test("Stage 6 workflow: default request never mutates", () => {
  assert.deepEqual(validateLibraryRequest({ operation: "validate" }), { operation: "validate", mutates: false });
  assert.deepEqual(validateLibraryRequest({ operation: "inspect" }), { operation: "inspect", mutates: false });
});
test("Stage 6 workflow: exact owner-authorized operations and pinned target IDs", () => {
  const good = [
    { operation: "add-track", track_id: "144530503", duration_ms: 180872, confirm_owner: true },
    { operation: "add-asset", duration_ms: 180872, confirm_owner: true, confirm_reviewed: true },
    { operation: "link", track_db_id: "1", asset_id: "1", confirm_owner: true },
    { operation: "approve", replacement_id: "12", confirm_owner: true, confirm_reviewed: true },
    { operation: "activate", replacement_id: "12", expected_active_replacement_id: "0", confirm_owner: true, confirm_activate: true },
    { operation: "disable", replacement_id: "12", expected_active_replacement_id: "12", confirm_owner: true, confirm_disable: true }
  ];
  for (const candidate of good) assert.equal(validateLibraryRequest(candidate).mutates, true);
});
test("Stage 6 workflow: no arbitrary command, external path or unconfirmed writes", () => {
  const invalid = [
    { operation: "shell", command: "id" },
    { operation: "validate", host: "external" },
    { operation: "inspect", track_id: "2" },
    { operation: "add-track", track_id: "00123", duration_ms: 1000, confirm_owner: true },
    { operation: "add-track", track_id: "1", duration_ms: -1, confirm_owner: true },
    { operation: "add-track", track_id: "1", duration_ms: 1000, confirm_owner: false },
    { operation: "add-asset", duration_ms: 1000, file: "/private/secret.mp3", confirm_owner: true, confirm_reviewed: true },
    { operation: "add-asset", duration_ms: 1000, confirm_owner: true },
    { operation: "link", track_db_id: "-1", asset_id: "1", confirm_owner: true },
    { operation: "link", track_db_id: "1;DROP TABLE", asset_id: "1", confirm_owner: true },
    { operation: "activate", replacement_id: "1", expected_active_replacement_id: "0", confirm_owner: true },
    { operation: "activate", replacement_id: "1", expected_active_replacement_id: "xyz", confirm_owner: true, confirm_activate: true },
    { operation: "disable", replacement_id: "1", expected_active_replacement_id: "1", confirm_owner: true, confirm_disable: "true" },
    null, [], { operation: "unknown" }
  ];
  for (const candidate of invalid) assert.throws(() => validateLibraryRequest(candidate));
});
