import { test } from "node:test";
import assert from "node:assert/strict";
import { homedir } from "node:os";
import { assessOfficialCompatibility, W6_PINNED_OWNER_IDENTITY } from "./compatibility.mjs";
import { createSyntheticRollbackLab, openSyntheticRollbackLab } from "./rollback-fixture.mjs";

const known = {
  osBuild: 19045, architecture: "X64", exeVersion: "5.126.1.0",
  packageVersion: "5.126.1", asarState: "OK",
  asarSha256: W6_PINNED_OWNER_IDENTITY.asarSha256,
  installed: true, running: true
};
const noWrite = result => {
  assert.equal(result.mayEditOfficialFiles, false);
  assert.equal(result.mayAttachToLiveRenderer, false);
  assert.equal(result.nativeSourceCompatibility, "UNPROVEN");
};

test("W6 real W3 owner identity only — no permission to patch", () => {
  const result = assessOfficialCompatibility(known);
  assert.equal(result.identity, "MATCHING_W3_IDENTITY_ONLY");
  assert.equal(result.reasons.length, 0);
  noWrite(result);
});

test("W6 updated Yandex executable or app.asar disables compatibility", () => {
  for (const changed of [
    { exeVersion: "5.126.2.0" }, { packageVersion: "5.126.2" },
    { asarSha256: "0".repeat(64) }, { asarState: "READ_FAILED" },
    { installed: false }, { running: false },
    { osBuild: 22000 }, { architecture: "ARM64" }
  ]) {
    const result = assessOfficialCompatibility({ ...known, ...changed });
    assert.equal(result.identity, "NOT_COMPATIBLE_OR_UNKNOWN");
    assert.ok(result.reasons.length > 0);
    noWrite(result);
  }
});

test("W6 matching static marker is not live renderer integration", () => {
  const result = assessOfficialCompatibility({
    ...known, rendererEvidence: "getFileInfo string hint True",
    playback: "native W5 isolated test succeeded"
  });
  assert.equal(result.identity, "MATCHING_W3_IDENTITY_ONLY");
  assert.equal(result.rollbackOnOwnerMachine, "UNTESTED");
  noWrite(result);
});

test("W6 rollback refuses arbitrary outside directory", async () => {
  await assert.rejects(openSyntheticRollbackLab(homedir()), /W6_OUTSIDE_SYNTHETIC_TEMP/);
});

async function withLab(fn) {
  const lab = await createSyntheticRollbackLab();
  try { await fn(lab); }
  finally { await lab.close(); }
}
const original = async lab => {
  const result = await lab.inspect();
  assert.equal(result.state, "ORIGINAL");
  assert.equal(result.currentMatchesOriginal, true);
  assert.equal(result.backupMatchesOriginal, true);
};

test("W6 synthetic backup, apply, byte-checked restore, idempotency", async () =>
  withLab(async lab => {
    await original(lab);
    assert.equal(await lab.applyFixture(), "SYNTHETIC_APPLIED");
    const changed = await lab.inspect();
    assert.equal(changed.state, "APPLIED");
    assert.equal(changed.currentMatchesOriginal, false);
    assert.equal(changed.backupMatchesOriginal, true);
    assert.equal(await lab.restore(), "BYTE_VERIFIED_ORIGINAL");
    await original(lab);
    assert.equal(await lab.restore(), "ALREADY_ORIGINAL");
  }));

test("W6 synthetic double installation refused", async () =>
  withLab(async lab => {
    await lab.applyFixture();
    await assert.rejects(lab.applyFixture(), /W6_NOT_CLEAN/);
    assert.equal(await lab.restore(), "BYTE_VERIFIED_ORIGINAL");
  }));

for (const phase of ["after-journal", "after-park", "after-promote"]) {
  test("W6 crash during synthetic install is recoverable: " + phase, async () =>
    withLab(async lab => {
      await assert.rejects(lab.applyFixture({ faultAt: phase }), /W6_SIMULATED_POWER_LOSS/);
      const reopened = await lab.restart();
      assert.equal(await reopened.restore(), "BYTE_VERIFIED_ORIGINAL");
      await original(reopened);
    }));
  test("W6 crash during synthetic restore is recoverable: " + phase, async () =>
    withLab(async lab => {
      await lab.applyFixture();
      await assert.rejects(lab.restore({ faultAt: phase }),
        /W6_SIMULATED_RESTORE_POWER_LOSS/);
      const reopened = await lab.restart();
      assert.equal(await reopened.restore(), "BYTE_VERIFIED_ORIGINAL");
      await original(reopened);
    }));
}

test("W6 new Yandex-like update blocks fixture apply without overwriting it", async () =>
  withLab(async lab => {
    await lab.simulateUnknownUpdate();
    await assert.rejects(lab.applyFixture(), /W6_VERSION_OR_ARCHIVE_CHANGED/);
    const state = await lab.inspect();
    assert.equal(state.currentMatchesOriginal, false);
    assert.equal(state.backupMatchesOriginal, true);
  }));

test("W6 third-party change after apply blocks rollback instead of clobbering", async () =>
  withLab(async lab => {
    await lab.applyFixture();
    await lab.simulateUnknownUpdate();
    await assert.rejects(lab.restore(), /W6_UNKNOWN_UPDATE_REFUSE_OVERWRITE/);
    const state = await lab.inspect();
    assert.equal(state.currentMatchesOriginal, false);
    assert.equal(state.backupMatchesOriginal, true);
  }));

test("W6 corrupt backup is a hard-stop, never claim restored", async () =>
  withLab(async lab => {
    await lab.applyFixture();
    await lab.simulateCorruptBackup();
    await assert.rejects(lab.restore(), /W6_CORRUPTED_BACKUP/);
    const state = await lab.inspect();
    assert.equal(state.currentMatchesOriginal, false);
    assert.equal(state.backupMatchesOriginal, false);
  }));
