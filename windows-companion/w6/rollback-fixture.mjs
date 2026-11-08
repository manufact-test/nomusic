/**
 * W6 SYNTHETIC rollback laboratory. This cannot accept an installation path.
 *
 * Works only inside a freshly generated OS-temp directory and on files named
 * synthetic-client.bin. No Yandex executable, app.asar, user profile or
 * external project path is ever passed to a write operation.
 */
import { promises as fs, constants } from "node:fs";
import { createHash, randomBytes } from "node:crypto";
import { tmpdir } from "node:os";
import { basename, join, resolve, sep } from "node:path";

const PREFIX = "celikom-w6-synthetic-";
const MARKER = "CELIKOM-W6-SYNTHETIC-LAB-v1\n";
const F = Object.freeze({
  original: "synthetic-client.bin",
  backup: "verified-original.bin",
  journal: "transaction.json",
  staged: "staged-fixture.bin",
  parked: "parked-fixture.bin",
  restore: "staged-restore.bin",
  marker: "synthetic-only.marker"
});
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const readHash = async path => sha(await fs.readFile(path));
const present = async path => fs.stat(path).then(() => true, e => {
  if (e.code === "ENOENT") return false;
  throw e;
});
const abort = code => { throw Error("W6_" + code); };

async function assertSandboxRoot(root) {
  if (typeof root !== "string") abort("INVALID_SANDBOX");
  const r = resolve(root), t = resolve(tmpdir());
  if (!r.startsWith(t + sep) || !basename(r).startsWith(PREFIX))
    abort("OUTSIDE_SYNTHETIC_TEMP");
  const real = await fs.realpath(r);
  if (real !== r) abort("SANDBOX_SYMLINK");
  const stat = await fs.lstat(real);
  if (!stat.isDirectory() || stat.isSymbolicLink()) abort("SANDBOX_NOT_DIRECTORY");
  if ((await fs.readFile(join(real, F.marker), "utf8")) !== MARKER)
    abort("SANDBOX_MARKER_MISSING");
  for (const filename of Object.values(F)) {
    const path = join(real, filename);
    if (!(await present(path))) continue;
    const s = await fs.lstat(path);
    if (!s.isFile() || s.isSymbolicLink()) abort("SANDBOX_FILE_NOT_REGULAR");
  }
  return real;
}

async function atomicJournal(root, record) {
  const temp = join(root, "transaction.tmp");
  await fs.writeFile(temp, JSON.stringify(record) + "\n", { flag: "wx" });
  try { await fs.rename(temp, join(root, F.journal)); }
  finally { await fs.rm(temp, { force: true }); }
}

export async function createSyntheticRollbackLab() {
  const root = await fs.mkdtemp(join(tmpdir(), PREFIX));
  const bytes = Buffer.from("SYNTHETIC ELECTRON TEST\n" + randomBytes(16).toString("hex") + "\n");
  await fs.writeFile(join(root, F.marker), MARKER, { flag: "wx" });
  await fs.writeFile(join(root, F.original), bytes, { flag: "wx" });
  await fs.copyFile(join(root, F.original), join(root, F.backup), constants.COPYFILE_EXCL);
  const originalHash = sha(bytes);
  if (await readHash(join(root, F.backup)) !== originalHash)
    abort("BACKUP_VERIFICATION_FAILED");
  await fs.writeFile(join(root, F.journal), JSON.stringify({
    schema: 1, state: "ORIGINAL", originalHash, patchedHash: null
  }) + "\n", { flag: "wx" });
  return openSyntheticRollbackLab(root);
}

export async function openSyntheticRollbackLab(root) {
  root = await assertSandboxRoot(root);
  const file = filename => join(root, filename);
  const record = async () => {
    const j = JSON.parse(await fs.readFile(file(F.journal), "utf8"));
    if (j.schema !== 1 || !["ORIGINAL", "INSTALL_PENDING", "APPLIED", "RESTORE_PENDING"].includes(j.state) ||
        !/^[0-9a-f]{64}$/.test(j.originalHash) ||
        (j.patchedHash !== null && !/^[0-9a-f]{64}$/.test(j.patchedHash)))
      abort("UNTRUSTED_JOURNAL");
    return j;
  };
  const verifyBackup = async j => {
    await assertSandboxRoot(root);
    if (await readHash(file(F.backup)) !== j.originalHash)
      abort("CORRUPTED_BACKUP");
  };
  const inspectFile = async name =>
    (await present(file(name))) ? await readHash(file(name)) : null;
  const clear = async names => {
    for (const n of names) await fs.rm(file(n), { force: true });
  };

  return Object.freeze({
    // Only returns non-sensitive test status, never a real path.
    async inspect() {
      await assertSandboxRoot(root);
      const j = await record();
      return { state: j.state, currentMatchesOriginal: (await inspectFile(F.original)) === j.originalHash,
        backupMatchesOriginal: (await inspectFile(F.backup)) === j.originalHash };
    },
    async applyFixture({ faultAt = null } = {}) {
      await assertSandboxRoot(root);
      const j = await record();
      if (j.state !== "ORIGINAL") abort("NOT_CLEAN");
      await verifyBackup(j);
      if (await inspectFile(F.original) !== j.originalHash)
        abort("VERSION_OR_ARCHIVE_CHANGED");
      const source = await fs.readFile(file(F.original));
      // This is NOT an ASAR patch. It changes a fake byte buffer only.
      const changed = Buffer.concat([source, Buffer.from("W6-SYNTHETIC-ADAPTER-ONLY\n")]);
      const patchedHash = sha(changed);
      await fs.writeFile(file(F.staged), changed, { flag: "wx" });
      if (await readHash(file(F.staged)) !== patchedHash) abort("STAGE_INVALID");
      await atomicJournal(root, { ...j, state: "INSTALL_PENDING", patchedHash });
      if (faultAt === "after-journal") abort("SIMULATED_POWER_LOSS");
      await fs.rename(file(F.original), file(F.parked));
      if (faultAt === "after-park") abort("SIMULATED_POWER_LOSS");
      await fs.rename(file(F.staged), file(F.original));
      if (faultAt === "after-promote") abort("SIMULATED_POWER_LOSS");
      if (await readHash(file(F.original)) !== patchedHash) abort("PATCH_VERIFY_FAILED");
      await clear([F.parked]);
      await atomicJournal(root, { ...j, state: "APPLIED", patchedHash });
      return "SYNTHETIC_APPLIED";
    },
    async restore({ faultAt = null } = {}) {
      await assertSandboxRoot(root);
      const j = await record();
      await verifyBackup(j);
      const current = await inspectFile(F.original);
      if (current && current !== j.originalHash && current !== j.patchedHash)
        abort("UNKNOWN_UPDATE_REFUSE_OVERWRITE");
      if (j.state === "ORIGINAL") {
        if (current !== j.originalHash) abort("ORIGINAL_STATE_MISMATCH");
        return "ALREADY_ORIGINAL";
      }
      if (current === j.originalHash) {
        await clear([F.staged, F.parked, F.restore]);
        await atomicJournal(root, { ...j, state: "ORIGINAL", patchedHash: null });
        return "BYTE_VERIFIED_ORIGINAL";
      }
      if (current === null && (await inspectFile(F.parked)) !== j.originalHash &&
          (await inspectFile(F.parked)) !== j.patchedHash)
        abort("UNKNOWN_INTERRUPTED_STATE");

      // For the synthetic lab only: prepare a verified restore before changing
      // the current mock file. Any external modifications block restoration.
      await clear([F.restore]);
      await fs.copyFile(file(F.backup), file(F.restore), constants.COPYFILE_EXCL);
      if (await readHash(file(F.restore)) !== j.originalHash)
        abort("RESTORE_STAGE_INVALID");
      await atomicJournal(root, { ...j, state: "RESTORE_PENDING" });
      if (faultAt === "after-journal") abort("SIMULATED_RESTORE_POWER_LOSS");
      if (current !== null) {
        await clear([F.parked]);
        await fs.rename(file(F.original), file(F.parked));
      }
      if (faultAt === "after-park") abort("SIMULATED_RESTORE_POWER_LOSS");
      await fs.rename(file(F.restore), file(F.original));
      if (faultAt === "after-promote") abort("SIMULATED_RESTORE_POWER_LOSS");
      if (await readHash(file(F.original)) !== j.originalHash)
        abort("RESTORED_BYTES_DIFFER");
      await clear([F.staged, F.parked]);
      await atomicJournal(root, { ...j, state: "ORIGINAL", patchedHash: null });
      return "BYTE_VERIFIED_ORIGINAL";
    },
    // Fault-injection is allowed only on this fake file, never app.asar.
    async simulateUnknownUpdate() {
      await assertSandboxRoot(root);
      await fs.appendFile(file(F.original), "ANOTHER-INDEPENDENT-UPDATE\n");
    },
    async simulateCorruptBackup() {
      await assertSandboxRoot(root);
      await fs.appendFile(file(F.backup), "BAD-BACKUP\n");
    },
    async simulateMissingMarker() {
      await fs.rm(file(F.marker));
    },
    async restart() { return openSyntheticRollbackLab(root); },
    async close() {
      await assertSandboxRoot(root);
      await fs.rm(root, { recursive: true, force: true });
    }
  });
}
