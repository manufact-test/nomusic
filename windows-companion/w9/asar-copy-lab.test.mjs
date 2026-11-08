import { test } from "node:test";
import assert from "node:assert/strict";
import { homedir } from "node:os";
import {
  createGeneratedAsarLab, openGeneratedAsarLab,
  asarHeaderDigest, assessArchiveIntegrity
} from "./asar-copy-lab.mjs";

const clean = async lab => {
  const s = await lab.report();
  assert.equal(s.scope,"GENERATED_ASAR_TEST_ONLY");
  assert.equal(s.state,"ORIGINAL");
  assert.equal(s.activeIsOriginal,true);
  assert.equal(s.originalByteMatchesBackup,true);
  assert.equal(s.officialExecutableModified,false);
};
const withLab = async fn => {
  const lab=await createGeneratedAsarLab();
  try{await fn(lab);}finally{await lab.close();}
};

test("W9 genuine generated ASAR starts as exact backup verified by SHA",async()=>
  withLab(async lab=>{await clean(lab);}));

test("W9 rejects user paths; no API accepts official Yandex source archive",async()=>
  assert.rejects(openGeneratedAsarLab(homedir()),/W9_REFUSE_NON_SYNTHETIC_PATH/));

test("W9 malformed ASAR header must never be mistaken for trusted",()=>{
  assert.throws(()=>asarHeaderDigest(Buffer.from("garbage")) ,/W9_BAD_ASAR_BYTES/);
  const b=Buffer.alloc(40);
  b.writeUInt32LE(10000,12);
  assert.throws(()=>asarHeaderDigest(b),/W9_BAD_ASAR_HEADER/);
});

test("W9 unknown Windows EXE fuse or integrity resource BLOCKS official patch",()=>{
  const first="1".repeat(64),second="2".repeat(64);
  for(const options of [
    {},{embeddedAsarIntegrityValidation:true},
    {embeddedAsarIntegrityValidation:false},
    {executableIntegrityResource:"NONE_VERIFIED"}
  ]){
    const d=assessArchiveIntegrity({originalHeaderSha:first,candidateHeaderSha:second,...options});
    assert.equal(d.mayPatchOfficial,false);
    assert.equal(d.decision,"NO_GO_INTEGRITY_NOT_VERIFIED");
  }
  const fixtureOnly=assessArchiveIntegrity({originalHeaderSha:first,candidateHeaderSha:second,
    embeddedAsarIntegrityValidation:false,executableIntegrityResource:"NONE_VERIFIED"});
  assert.equal(fixtureOnly.decision,"SYNTHETIC_LAB_ONLY");
  assert.equal(fixtureOnly.mayPatchOfficial,false);
});

test("W9 repacks only synthetic copy, detects changed header, and restores exact bytes",async()=>
  withLab(async lab=>{
    await clean(lab);
    const patched=await lab.prepareModifiedCopy();
    assert.equal(patched.state,"SYNTHETIC_COPY_PATCHED");
    assert.equal(patched.headerChanged,true);
    assert.equal(patched.mayPatchOfficial,false);
    assert.equal(patched.integrityDecision,"NO_GO_INTEGRITY_NOT_VERIFIED");
    const status=await lab.report();
    assert.equal(status.state,"COPY_APPLIED");
    assert.equal(status.activeIsKnownPatched,true);
    assert.equal(status.activeIsOriginal,false);
    assert.equal(await lab.restoreOriginal(),"BYTE_VERIFIED_ORIGINAL");
    await clean(lab);
    assert.equal(await lab.restoreOriginal(),"ALREADY_ORIGINAL");
  }));

test("W9 no double modification even if the candidate is valid",async()=>
  withLab(async lab=>{
    await lab.prepareModifiedCopy();
    await assert.rejects(lab.prepareModifiedCopy(),/W9_COPY_ALREADY_MODIFIED/);
    await lab.restoreOriginal();
    await clean(lab);
  }));

for(const phase of ["after-journal","after-park","after-promote"]){
  test("W9 generated ASAR survives simulated install interruption: "+phase,async()=>
    withLab(async lab=>{
      await assert.rejects(lab.prepareModifiedCopy({faultAt:phase}),
        /W9_SIMULATED_INTERRUPTION/);
      const reopened=await lab.restart();
      assert.equal(await reopened.restoreOriginal(),"BYTE_VERIFIED_ORIGINAL");
      await clean(reopened);
    }));
  test("W9 generated ASAR survives simulated restore interruption: "+phase,async()=>
    withLab(async lab=>{
      await lab.prepareModifiedCopy();
      await assert.rejects(lab.restoreOriginal({faultAt:phase}),
        /W9_SIMULATED_RESTORE_INTERRUPTION/);
      const reopened=await lab.restart();
      assert.equal(await reopened.restoreOriginal(),"BYTE_VERIFIED_ORIGINAL");
      await clean(reopened);
    }));
}

test("W9 unexpected third-party update to clean copy prevents patch",async()=>
  withLab(async lab=>{
    await lab.simulateUnrecognizedCopyUpdate();
    await assert.rejects(lab.prepareModifiedCopy(),/W9_COPY_UNKNOWN_UPDATE/);
  }));

test("W9 unexpected update to modified copy blocks rollback instead of overwrite",async()=>
  withLab(async lab=>{
    await lab.prepareModifiedCopy();
    await lab.simulateUnrecognizedCopyUpdate();
    await assert.rejects(lab.restoreOriginal(),/W9_THIRD_PARTY_CHANGE_REFUSE_OVERWRITE/);
  }));

test("W9 corrupted independent original backup stops restoration",async()=>
  withLab(async lab=>{
    await lab.prepareModifiedCopy();
    await lab.simulateBackupCorruption();
    await assert.rejects(lab.restoreOriginal(),/W9_ORIGINAL_BACKUP_INVALID/);
  }));
