/**
 * W9 physical ASAR trial -- only generated test archives inside unique OS
 * temp directories, NEVER a real Yandex app.asar or any EXE.
 *
 * Public operations cannot accept user archives or patch arbitrary paths.
 * This proves byte-for-byte sandbox recovery, NOT signed client compatibility.
 */
import { createRequire } from "node:module";
import { promises as fs, constants } from "node:fs";
import { createHash, randomBytes } from "node:crypto";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const require = createRequire(new URL("../w5/package.json", import.meta.url));
const { createPackage, extractAll } = require("@electron/asar");
const here = dirname(fileURLToPath(import.meta.url));
const PREFIX = "celikom-w9-generated-asar-only-";
const MARKER = "CELIKOM-W9-GENERATED-ONLY-v1\n";
const N = Object.freeze({
  marker: ".W9-ONLY",
  original: "original.asar",
  backup: "original-backup.asar",
  active: "copy-app.asar",
  pending: "pending.asar",
  parked: "parked-original.asar",
  retired: "retired-copy.asar",
  restage: "pending-restore.asar",
  journal: "journal.json"
});
const SHA = value => createHash("sha256").update(value).digest("hex");
const throwCode = code => { throw Error("W9_" + code); };
const exists = async path => fs.lstat(path).then(() => true, error => {
  if (error.code === "ENOENT") return false;
  throw error;
});
const bytes = async path => fs.readFile(path);
const hash = async path => (await exists(path)) ? SHA(await bytes(path)) : null;
const sameSha = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const internal = (root, name) => join(root, N[name]);

export function asarHeaderDigest(raw) {
  if (!Buffer.isBuffer(raw) || raw.length < 20) throwCode("BAD_ASAR_BYTES");
  const length = raw.readUInt32LE(12);
  if (!length || length > 16 * 1024 * 1024 ||
      16 + Math.ceil(length / 4) * 4 >= raw.length) throwCode("BAD_ASAR_HEADER");
  return SHA(raw.subarray(16, 16 + length));
}

export function assessArchiveIntegrity({
  originalHeaderSha, candidateHeaderSha,
  embeddedAsarIntegrityValidation = "UNKNOWN",
  executableIntegrityResource = "UNKNOWN"
}) {
  if (!sameSha(originalHeaderSha) || !sameSha(candidateHeaderSha))
    return Object.freeze({ decision: "NO_GO_UNVERIFIED_HEADER", mayPatchOfficial: false });
  if (originalHeaderSha !== candidateHeaderSha &&
      (embeddedAsarIntegrityValidation !== false ||
       executableIntegrityResource !== "NONE_VERIFIED"))
    return Object.freeze({
      decision: "NO_GO_INTEGRITY_NOT_VERIFIED",
      mayPatchOfficial: false,
      mayLaunchDisposableUnsignedFixture: true
    });
  return Object.freeze({
    decision: "SYNTHETIC_LAB_ONLY",
    mayPatchOfficial: false,
    mayLaunchDisposableUnsignedFixture: true
  });
}

async function assertRoot(root) {
  if (typeof root !== "string") throwCode("REFUSE_NON_SYNTHETIC_PATH");
  const path = resolve(root);
  const tmp = resolve(tmpdir());
  const rel = relative(tmp, path);
  if (!rel || rel === ".." || rel.startsWith(".." + sep) ||
      isAbsolute(rel) || !basename(path).startsWith(PREFIX))
    throwCode("REFUSE_NON_SYNTHETIC_PATH");
  const stat = await fs.lstat(path);
  if (!stat.isDirectory() || stat.isSymbolicLink()) throwCode("ROOT_NOT_REAL_DIRECTORY");
  const realTemp = await fs.realpath(tmp), realRoot = await fs.realpath(path);
  const canonical = relative(realTemp, realRoot);
  if (!canonical || canonical === ".." || canonical.startsWith(".." + sep) ||
      isAbsolute(canonical) || !basename(realRoot).startsWith(PREFIX))
    throwCode("ROOT_OUTSIDE_TEMP");
  if (await fs.readFile(internal(path,"marker"),"utf8") !== MARKER)
    throwCode("INVALID_GENERATED_MARKER");
  for (const name of ["original","backup","active","pending","parked","retired","restage","journal"]) {
    const file = internal(path,name);
    if (!(await exists(file))) continue;
    const e = await fs.lstat(file);
    if (!e.isFile() || e.isSymbolicLink()) throwCode("UNSAFE_FILE_NODE");
  }
  const work = join(path,"work");
  if (await exists(work)) {
    const e = await fs.lstat(work);
    if (!e.isDirectory() || e.isSymbolicLink()) throwCode("UNSAFE_WORK_DIRECTORY");
  }
  return path;
}

async function getJournal(root) {
  const j = JSON.parse(await fs.readFile(internal(root,"journal"),"utf8"));
  if (j.schema !== 1 || !["ORIGINAL","INSTALL_PENDING","COPY_APPLIED","RESTORE_PENDING"].includes(j.state) ||
      !sameSha(j.originalSha) || !sameSha(j.originalHeaderSha) ||
      !(j.modifiedSha === null || sameSha(j.modifiedSha))) throwCode("INVALID_GENERATED_JOURNAL");
  return j;
}

async function journal(root, value) {
  const temp = join(root,".journal-stage-"+randomBytes(6).toString("hex"));
  await fs.writeFile(temp,JSON.stringify(value)+"\n",{flag:"wx"});
  try { await fs.rename(temp,internal(root,"journal")); }
  finally { await fs.rm(temp,{force:true}); }
}

async function checkBackup(root, record) {
  if (await hash(internal(root,"original")) !== record.originalSha ||
      await hash(internal(root,"backup")) !== record.originalSha)
    throwCode("ORIGINAL_BACKUP_INVALID");
  if (asarHeaderDigest(await bytes(internal(root,"original"))) !== record.originalHeaderSha)
    throwCode("ORIGINAL_HEADER_CHANGED");
}

async function cleanup(root) {
  for (const key of ["pending","parked","retired","restage"]) await fs.rm(internal(root,key),{force:true});
  await fs.rm(join(root,"work"),{recursive:true,force:true});
}

export async function createGeneratedAsarLab() {
  const root = await fs.mkdtemp(join(tmpdir(),PREFIX));
  // No caller-controlled source or arbitrary input path: pack only the
  // precisely named local fixture application checked into Windows W9.
  await fs.writeFile(internal(root,"marker"),MARKER,{flag:"wx"});
  await createPackage(join(here,"fixture-app"),internal(root,"original"));
  const original = await bytes(internal(root,"original"));
  await fs.copyFile(internal(root,"original"),internal(root,"backup"),constants.COPYFILE_EXCL);
  await fs.copyFile(internal(root,"original"),internal(root,"active"),constants.COPYFILE_EXCL);
  const originalSha = SHA(original);
  if (await hash(internal(root,"backup")) !== originalSha ||
      await hash(internal(root,"active")) !== originalSha) throwCode("INITIAL_COPY_INVALID");
  await fs.writeFile(internal(root,"journal"),JSON.stringify({
    schema:1,state:"ORIGINAL",originalSha,originalHeaderSha:asarHeaderDigest(original),modifiedSha:null
  })+"\n",{flag:"wx"});
  return openGeneratedAsarLab(root);
}

export async function openGeneratedAsarLab(root) {
  root = await assertRoot(root);
  const path = key => internal(root,key);
  const checkedRecord = async () => {
    await assertRoot(root);
    const j = await getJournal(root);
    await checkBackup(root,j);
    return j;
  };

  return Object.freeze({
    // This path belongs to an ephemeral, generated test app. Never pass a
    // Yandex installation path or another archive to this interface.
    async generatedTestAppPath() {
      await checkedRecord();
      return path("active");
    },
    async report() {
      const record = await checkedRecord();
      const current = await hash(path("active"));
      return {
        scope:"GENERATED_ASAR_TEST_ONLY", state:record.state,
        originalByteMatchesBackup:true,
        activeIsOriginal:current===record.originalSha,
        activeIsKnownPatched:current!==null && current===record.modifiedSha,
        headerIntegrityDecision:record.modifiedSha?assessArchiveIntegrity({
          originalHeaderSha:record.originalHeaderSha,
          candidateHeaderSha:asarHeaderDigest(await bytes(path("active"))),
          embeddedAsarIntegrityValidation:"UNKNOWN",
          executableIntegrityResource:"UNKNOWN"
        }).decision:"ORIGINAL_ONLY",
        officialExecutableModified:false
      };
    },
    async prepareModifiedCopy({ faultAt=null }={}) {
      const j=await checkedRecord();
      if (j.state!=="ORIGINAL") throwCode("COPY_ALREADY_MODIFIED");
      if (await hash(path("active"))!==j.originalSha) throwCode("COPY_UNKNOWN_UPDATE");
      if (await exists(path("pending")) || await exists(path("parked"))) throwCode("ORPHAN_STAGE_REFUSE");
      await fs.mkdir(join(root,"work"),{recursive:false});
      extractAll(path("active"),join(root,"work"));
      const filename=join(root,"work","index.cjs");
      const index=await fs.readFile(filename,"utf8");
      const slot="/* W9_SYNTHETIC_HOOK_SLOT */";
      if (index.split(slot).length!==2 || !index.includes("W9_GENERATED_TEST_APP_ONLY"))
        throwCode("UNSUPPORTED_APP_MAIN");
      const patched=index.replace(slot,slot+"\nrequire('./__celikom_w9_test_only.cjs');");
      await fs.writeFile(filename,patched);
      await fs.copyFile(join(here,"fixture-hook.cjs"),join(root,"work","__celikom_w9_test_only.cjs"),
        constants.COPYFILE_EXCL);
      await createPackage(join(root,"work"),path("pending"));
      const modified=await bytes(path("pending"));
      const modifiedSha=SHA(modified), headerSha=asarHeaderDigest(modified);
      if (modifiedSha===j.originalSha || headerSha===j.originalHeaderSha)
        throwCode("COPY_PACKAGING_NO_CHANGE");
      const integrity=assessArchiveIntegrity({
        originalHeaderSha:j.originalHeaderSha, candidateHeaderSha:headerSha,
        embeddedAsarIntegrityValidation:"UNKNOWN",executableIntegrityResource:"UNKNOWN"
      });
      if (integrity.mayPatchOfficial) throwCode("UNEXPECTED_OFFICIAL_WRITE_PERMISSION");
      await journal(root,{...j,state:"INSTALL_PENDING",modifiedSha});
      if (faultAt==="after-journal") throwCode("SIMULATED_INTERRUPTION");
      await fs.rename(path("active"),path("parked"));
      if (faultAt==="after-park") throwCode("SIMULATED_INTERRUPTION");
      await fs.rename(path("pending"),path("active"));
      if (faultAt==="after-promote") throwCode("SIMULATED_INTERRUPTION");
      if (await hash(path("active"))!==modifiedSha) throwCode("COPY_PATCH_BYTES_DID_NOT_MATCH");
      await journal(root,{...j,state:"COPY_APPLIED",modifiedSha});
      await fs.rm(path("parked"),{force:true});
      await fs.rm(join(root,"work"),{recursive:true,force:true});
      return {state:"SYNTHETIC_COPY_PATCHED",headerChanged:true,
        integrityDecision:integrity.decision,mayPatchOfficial:false};
    },
    async restoreOriginal({faultAt=null}={}) {
      const j=await checkedRecord();
      const current=await hash(path("active"));
      const parked=await hash(path("parked"));
      const retired=await hash(path("retired"));
      for (const value of [current,parked,retired]) {
        if (value && value!==j.originalSha && value!==j.modifiedSha)
          throwCode("THIRD_PARTY_CHANGE_REFUSE_OVERWRITE");
      }
      if (j.state==="ORIGINAL") {
        if (current!==j.originalSha) throwCode("ORIGINAL_EXPECTED_MISSING");
        return "ALREADY_ORIGINAL";
      }
      if (current===j.originalSha) {
        await cleanup(root);
        await journal(root,{...j,state:"ORIGINAL",modifiedSha:null});
        return "BYTE_VERIFIED_ORIGINAL";
      }
      // A crash after original was parked but before candidate promotion
      // may leave no active archive. Always restore from an independent
      // backup rather than reusing an unknown stranded stage.
      await fs.rm(path("restage"),{force:true});
      await fs.copyFile(path("backup"),path("restage"),constants.COPYFILE_EXCL);
      if (await hash(path("restage"))!==j.originalSha) throwCode("RESTORE_STAGING_INVALID");
      await journal(root,{...j,state:"RESTORE_PENDING"});
      if (faultAt==="after-journal") throwCode("SIMULATED_RESTORE_INTERRUPTION");
      if (current!==null) {
        // Retired only contains previously checked fixture bytes.
        await fs.rm(path("retired"),{force:true});
        await fs.rename(path("active"),path("retired"));
      }
      if (faultAt==="after-park") throwCode("SIMULATED_RESTORE_INTERRUPTION");
      await fs.rename(path("restage"),path("active"));
      if (faultAt==="after-promote") throwCode("SIMULATED_RESTORE_INTERRUPTION");
      if (await hash(path("active"))!==j.originalSha ||
          asarHeaderDigest(await bytes(path("active")))!==j.originalHeaderSha)
        throwCode("RESTORE_BYTES_DIFFER");
      await cleanup(root);
      await journal(root,{...j,state:"ORIGINAL",modifiedSha:null});
      return "BYTE_VERIFIED_ORIGINAL";
    },
    async simulateUnrecognizedCopyUpdate() {
      await checkedRecord();
      await fs.appendFile(path("active"),"W9_OUTSIDE_CHANGE\n");
    },
    async simulateBackupCorruption() {
      await checkedRecord();
      await fs.appendFile(path("backup"),"W9_CORRUPT_BACKUP\n");
    },
    async restart() { return openGeneratedAsarLab(root); },
    async close() {
      await assertRoot(root);
      await fs.rm(root,{recursive:true,force:true});
    }
  });
}
