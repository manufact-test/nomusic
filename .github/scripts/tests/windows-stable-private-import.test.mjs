import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync,sign,createHash} from "node:crypto";
import {mkdtemp,mkdir,writeFile,readFile,readlink,readdir,rm,symlink,chmod} from "node:fs/promises";
import {join} from "node:path";
import {tmpdir} from "node:os";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import {promoteLocalFeed} from "../windows-stable-publish-floki.mjs";
const cli=fileURLToPath(new URL("../windows-stable-private-import.py",import.meta.url));
const intake=fileURLToPath(new URL("../windows-stable-private-intake.py",import.meta.url));
const sha=b=>createHash("sha256").update(b).digest("hex");
const run=(args,input)=>spawnSync("python3",[cli,...args],{input,encoding:"utf8",maxBuffer:1024*1024,timeout:120000});
test("private Windows transport verifies signed identity, monotonic floor, archive boundaries and never changes current",async t=>{
  if(process.platform==="win32")return t.skip("Linux receiver contract");
  const dir=await mkdtemp(join(tmpdir(),"celikom-private-transfer-"));t.after(()=>rm(dir,{recursive:true,force:true}));
  const floor=join(dir,"stable"),dest=join(dir,"import"),pin=join(dir,"pin.der");
  await mkdir(floor,{mode:0o700});await mkdir(dest,{mode:0o700});
  const pair=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  const pub=pair.publicKey.export({format:"der",type:"spki"});await writeFile(pin,pub,{mode:0o600});
  async function fixture(name,version,sequence){
    const source=join(dir,name);await mkdir(source,{mode:0o700});await mkdir(join(source,version),{mode:0o700});
    const app="CELIKOM-Windows-"+version+".exe",bytes=Buffer.alloc(11000,sequence);
    const data={schema:2,channel:"stable",publisher:"CELIKOM",version,sequence,
      packageUrl:"https://celikom.com/CELIKOM/Windows/Updates/stable/"+version+"/"+app,
      packageSize:bytes.length,sha256:sha(bytes),publishedAt:new Date(Date.now()-60000).toISOString(),
      expiresAt:new Date(Date.now()+86400000).toISOString(),minimumVersion:null,mandatory:false,notes:"",rollback:null,
      applicationSha256:"1".repeat(64),nativeHostSha256:"2".repeat(64),rendererSha256:"3".repeat(64),supervisorSha256:"4".repeat(64)};
    const doc=Buffer.from(JSON.stringify(data)),sig=sign("sha256",doc,{key:pair.privateKey,dsaEncoding:"der"});
    for(const [file,value] of [["latest.json",doc],["latest.json.sig",sig],["manifest-public-key.der",pub],[version+"/manifest.json",doc],[version+"/manifest.json.sig",sig],[version+"/"+app,bytes]])await writeFile(join(source,file),value,{mode:0o600});
    return {source,root:floor,version,sequence,pinnedPublicKeyDerBase64:pub.toString("base64"),app,bytes};
  }
  const first=await fixture("first","0.24.55",2);
  await promoteLocalFeed(first);
  async function pack(f,name){
    const path=join(dir,name+".zip");
    const result=run(["pack","--source",f.source,"--output",path,"--pin",pin,"--version",f.version,"--sequence",String(f.sequence)]);
    assert.equal(result.status,0,result.stderr);
    return readFile(path);
  }
  function receive(f,bytes){
    return run(["receive","--dest-root",dest,"--floor-root",floor,"--pin",pin,"--version",f.version,"--sequence",String(f.sequence)],bytes);
  }
  const next=await fixture("next","0.24.56",3);
  const bytes=await pack(next,"next");
  assert.deepEqual(await pack(next,"next-repeat"),bytes,"same signed release has deterministic transport bytes");
  // Test the real unprivileged receiver function on disposable data; the
  // remote entrypoint itself requires a nonroot uid and fixed server paths.
  const inbox=join(dir,"inbox");await mkdir(inbox,{mode:0o700});
  const intakeCall=(command,input)=>spawnSync("python3",["-c",
    "import runpy,sys,pathlib,os;m=runpy.run_path(sys.argv[1]);print(*m['receive'](sys.stdin.buffer,pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]),sys.argv[4],os.getuid()))",
    intake,inbox,pin,command],{input,encoding:"utf8",maxBuffer:1024*1024,timeout:120000});
  const command="stage-windows "+next.version+" "+next.sequence+" "+sha(bytes);
  let remote=intakeCall(command,bytes);
  assert.equal(remote.status,0,remote.stderr);assert.match(remote.stdout,/private-staged/);
  remote=intakeCall(command,bytes);assert.equal(remote.status,0,remote.stderr);assert.match(remote.stdout,/already-staged/);
  remote=intakeCall("maintenance",bytes);assert.notEqual(remote.status,0);assert.match(remote.stderr,/COMMAND_REFUSED/);
  remote=intakeCall(command+" ; id",bytes);assert.notEqual(remote.status,0);assert.match(remote.stderr,/COMMAND_REFUSED/);
  remote=intakeCall("stage-windows "+next.version+" "+next.sequence+" "+"0".repeat(64),bytes);assert.notEqual(remote.status,0);assert.match(remote.stderr,/TRANSFER_SHA_MISMATCH/);
  assert.deepEqual(await readFile(join(inbox,"windows-"+next.version+"-"+next.sequence+"-"+sha(bytes)+".zip")),bytes);
  assert.equal(await readlink(join(floor,"current")),"versions/0.24.55");

  let res=receive(next,bytes);
  assert.equal(res.status,0,res.stderr);assert.match(res.stdout,/private-staged/);
  assert.deepEqual(await readFile(join(dest,"windows-0.24.56",next.version,next.app)),next.bytes);
  res=receive(next,bytes);assert.equal(res.status,0,res.stderr);assert.match(res.stdout,/already-staged/);
  const oldBytes=await pack(first,"first");
  assert.equal(receive(first,oldBytes).status,0);
  const lower=await fixture("lower","0.24.54",1);
  res=receive(lower,await pack(lower,"lower"));assert.notEqual(res.status,0);assert.match(res.stderr,/NON_MONOTONIC_TRANSFER/);
  const replay=await fixture("replay","0.24.57",2);
  res=receive(replay,await pack(replay,"replay"));assert.notEqual(res.status,0);assert.match(res.stderr,/NON_MONOTONIC_TRANSFER/);
  // Extra ZIP member and traversal path are rejected before extracting any member.
  const evil=spawnSync("python3",["-c","import io,sys,zipfile;b=io.BytesIO(sys.stdin.buffer.read());z=zipfile.ZipFile(b,'a');z.writestr('../evil','x');z.close();sys.stdout.buffer.write(b.getvalue())"],{input:bytes,maxBuffer:1024*1024});
  assert.equal(evil.status,0);res=receive(next,evil.stdout);assert.notEqual(res.status,0);assert.match(res.stderr,/BAD_ZIP_DIRECTORY|UNEXPECTED_ARCHIVE_MEMBERS/);
  // Corrupt signed file inside a structurally valid ZIP.
  const corrupt=spawnSync("python3",["-c","import io,sys,zipfile;a=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));b=io.BytesIO();z=zipfile.ZipFile(b,'w');[(z.writestr(n,b'x'*len(a.read(n)) if n.endswith('.exe') else a.read(n))) for n in a.namelist()];z.close();sys.stdout.buffer.write(b.getvalue())"],{input:bytes,maxBuffer:1024*1024});
  assert.equal(corrupt.status,0);res=receive(next,corrupt.stdout);assert.notEqual(res.status,0);assert.match(res.stderr,/MANIFEST_POLICY_INVALID/);
  await chmod(dest,0o755);res=receive(next,bytes);assert.notEqual(res.status,0);assert.match(res.stderr,/UNSAFE_PRIVATE_DIRECTORY/);await chmod(dest,0o700);
  assert.equal(await readlink(join(floor,"current")),"versions/0.24.55");
  assert.deepEqual((await readdir(dest)).sort(),["windows-0.24.55","windows-0.24.56"]);
});
