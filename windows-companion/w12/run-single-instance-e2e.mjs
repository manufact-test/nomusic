/**
 * W12 Windows-only: two real GENERIC Electron processes, not official Yandex.
 * Demonstrate same-profile second-instance forwarding and separate-profile
 * isolation without account access or modifications to any installed app.
 */
import {createRequire} from "node:module";
import {mkdtemp,mkdir,writeFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join,resolve} from "node:path";
import {spawn} from "node:child_process";
import {randomBytes} from "node:crypto";
if(process.platform!=="win32")throw Error("W12_WINDOWS_CI_FIXTURE_ONLY");
const require=createRequire(new URL("../w5/package.json",import.meta.url));
const electron=require("electron");
const script=resolve(import.meta.dirname,"synthetic-single-instance.cjs");
const nonce=randomBytes(16).toString("hex");
const root=await mkdtemp(join(tmpdir(),"celikom-w12-generated-only-"));
const A=join(root,"profile-A"),B=join(root,"profile-B");
const children=[];
await writeFile(join(root,".w12-marker"),"CELIKOM-W12-GENERATED-ONLY\n");
await mkdir(A);await mkdir(B);
function launch(profile){
  const env={...process.env,CELIKOM_W12_FIXTURE_ONLY:"YES",
    CELIKOM_W12_NONCE:nonce,CELIKOM_W12_ROOT:root,CELIKOM_W12_PROFILE:profile};
  delete env.ELECTRON_RUN_AS_NODE;delete env.NODE_OPTIONS;
  const child=spawn(electron,[script],{env,cwd:resolve(import.meta.dirname,"../w5"),
    windowsHide:true,shell:false,stdio:["ignore","pipe","pipe"]});
  children.push(child);
  let buffer="";const lines=[],listeners=new Set();
  let done=false;
  function notify(line){
    if(!line)return;
    lines.push(line);
    for(const f of [...listeners])f(line);
  }
  child.stdout.on("data",chunk=>{
    buffer+=chunk.toString("utf8");
    if(buffer.length>12000){notify("W12_STDOUT_OVERFLOW");child.kill();return;}
    let i;
    while((i=buffer.indexOf("\n"))>=0){
      notify(buffer.slice(0,i).trim());buffer=buffer.slice(i+1);
    }
  });
  child.stderr.on("data",()=>{}); // never publish paths, profiles, stack trace
  child.once("close",()=>{done=true;notify("W12_EXITED");});
  return {
    child,lines,
    see(line,limit=15000){
      if(lines.includes(line))return Promise.resolve();
      if(done)return Promise.reject(Error("W12_EARLY_EXIT"));
      return new Promise((resolveWait,rejectWait)=>{
        const timer=setTimeout(()=>{listeners.delete(handler);rejectWait(Error("W12_TIMEOUT_"+line));},limit);
        const handler=x=>{
          if(x===line){clearTimeout(timer);listeners.delete(handler);resolveWait();}
          else if(x==="W12_EXITED"||x==="W12_STDOUT_OVERFLOW"){
            clearTimeout(timer);listeners.delete(handler);rejectWait(Error("W12_EARLY_EXIT"));
          }
        };
        listeners.add(handler);
      });
    }
  };
}
const checks=[];
try{
  const first=launch(A);
  await first.see("W12_PRIMARY_READY=1");
  checks.push("generic Electron first instance owns synthetic profile A");
  const duplicate=launch(A);
  await duplicate.see("W12_SECONDARY_DENIED=1");
  checks.push("second startup with same profile does not create a new player");
  await first.see("W12_SECOND_INSTANCE_FORWARDED=1");
  checks.push("second startup forwards to existing primary process");
  const separate=launch(B);
  await separate.see("W12_PRIMARY_READY=1");
  checks.push("distinct synthetic profile B acquires an independent lock");
  if(separate.lines.includes("W12_SECONDARY_DENIED=1"))
    throw Error("W12_PROFILE_B_COLLIDED");
  checks.push("distinct fixture profile does not masquerade as original process");
  console.log(JSON.stringify({
    w12:"PASS",scope:"GENERIC_ELECTRON_ONLY",assertions:checks.length,checks,
    sameProfileSecondInstance:"FORWARDED",separateProfile:"ISOLATED_SYNTHETIC",
    officialYandexStarted:false,officialYandexAttached:false,
    realAccountRead:false,officialFilesModified:false,
    officialYandexProfileIsolationProven:false
  },null,2));
}finally{
  for(const child of children)
    if(child.exitCode===null && !child.killed)child.kill();
  await Promise.all(children.map(c=>new Promise(done=>{
    if(c.exitCode!==null||c.signalCode!==null)return done();
    c.once("close",done);setTimeout(done,2500);
  })));
  await rm(root,{recursive:true,force:true,maxRetries:4,retryDelay:250});
}
