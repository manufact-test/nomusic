/**
 * W9 end-to-end Windows: physically boot original ASAR, patched COPY ASAR,
 * then independently restored ASAR using a generic Electron.exe from npm.
 *
 * The binary here is an independent, unsigned test Electron runtime.
 * Yandex Music is not launched, modified, copied or read.
 */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { createGeneratedAsarLab } from "./asar-copy-lab.mjs";

if (process.platform !== "win32")
  throw Error("W9_WINDOWS_ONLY_GENUINE_ELECTRON_LAUNCH");
const require = createRequire(new URL("../w5/package.json", import.meta.url));
const testElectron = require("electron");

const boot = path => new Promise((resolve,reject)=>{
  const env={...process.env, ELECTRON_NO_ATTACH_CONSOLE:"0"};
  delete env.ELECTRON_RUN_AS_NODE;
  delete env.NODE_OPTIONS;
  const child=spawn(testElectron,[path],{windowsHide:true,shell:false,env,
    stdio:["ignore","pipe","pipe"]});
  let out="",err="",settled=false;
  const fail=e=>{
    if(settled)return;
    settled=true;clearTimeout(timer);child.kill();
    reject(e);
  };
  const timer=setTimeout(()=>fail(Error("W9_BOOT_TIMEOUT")),30000);
  child.stdout.on("data",part=>{if(out.length<10000)out+=part.toString("utf8");});
  child.stderr.on("data",part=>{if(err.length<3000)err+=part.toString("utf8");});
  child.on("error",()=>fail(Error("W9_ELECTRON_SPAWN_FAILED")));
  child.on("close",code=>{
    if(settled)return;
    settled=true;clearTimeout(timer);
    if(code!==0)return reject(Error("W9_FIXTURE_APP_FAILED_"+code));
    const line=out.split(/\r?\n/).find(s=>s.startsWith("W9_SYNTHETIC_BOOT="));
    if(!line)return reject(Error("W9_NO_REAL_ELECTRON_BOOT_MARKER"));
    let result;
    try{result=JSON.parse(line.slice("W9_SYNTHETIC_BOOT=".length));}
    catch{return reject(Error("W9_INVALID_BOOT_REPORT"));}
    if(result.scope!=="ISOLATED_ASAR_FIXTURE_ONLY" ||
       result.officialYandexUsed!==false ||result.officialExeModified!==false||
       result.nativeMediaElements!==1||result.didStartActualElectron!==true)
      return reject(Error("W9_BOOT_NOT_ISOLATED"));
    resolve(result);
  });
});

const lab=await createGeneratedAsarLab();
try{
  const appPath=await lab.generatedTestAppPath();
  const checkpoints=[];
  const original=await boot(appPath);
  assert.equal(original.mode,"ORIGINAL");
  assert.equal(original.hookMarkerPresent,false);
  checkpoints.push("actual Electron boot of ORIGINAL generated app.asar");

  const staged=await lab.prepareModifiedCopy();
  assert.equal(staged.state,"SYNTHETIC_COPY_PATCHED");
  assert.equal(staged.headerChanged,true);
  assert.equal(staged.integrityDecision,"NO_GO_INTEGRITY_NOT_VERIFIED");
  assert.equal(staged.mayPatchOfficial,false);
  checkpoints.push("modified only separate synthetic copy, ASAR header SHA changed and official gate denied");

  const patched=await boot(appPath);
  assert.equal(patched.mode,"PATCHED_COPY");
  assert.equal(patched.hookMarkerPresent,true);
  checkpoints.push("actual Electron boot of modified copy loads test-only hook");

  assert.equal(await lab.restoreOriginal(),"BYTE_VERIFIED_ORIGINAL");
  const status=await lab.report();
  assert.equal(status.activeIsOriginal,true);
  assert.equal(status.originalByteMatchesBackup,true);
  checkpoints.push("byte-for-byte SHA-256 verified restore of copy from independent backup");

  const restored=await boot(appPath);
  assert.equal(restored.mode,"ORIGINAL");
  assert.equal(restored.hookMarkerPresent,false);
  checkpoints.push("actual Electron reboot of restored copy has NO test hook");

  console.log(JSON.stringify({
    w9:"PASS", kind:"GENUINE_GENERATED_ASAR_COPY_LAB",
    nativeElectronLaunched:true,
    originalBoot:"PASS",modifiedCopyBoot:"PASS",restoredBoot:"PASS",
    checkpoints, total:checkpoints.length,
    officialYandexUsed:false, officialExeModified:false,
    signedOfficialAppCompatibility:"UNTESTED",
    embeddedOfficialIntegrityFuse:"UNKNOWN"
  },null,2));
}finally{
  await lab.close();
}
