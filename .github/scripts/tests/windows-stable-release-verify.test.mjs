import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync,sign,createHash} from "node:crypto";
import {mkdtemp,mkdir,writeFile,readFile,rm,truncate,symlink} from "node:fs/promises";
import {execFileSync} from "node:child_process";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {verifyPreparedStableRelease} from "../windows-stable-release-verify.mjs";
import {verifyExistingStableLatest} from "../windows-stable-existing-latest.mjs";
const origin="https://celikom.com",version="0.24.38",sequence=1;
const sha=x=>createHash("sha256").update(x).digest("hex");
async function fixture(t){
  const root=await mkdtemp(join(tmpdir(),"celikom-w148-"));t.after(()=>rm(root,{recursive:true,force:true}));
  const pair=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  const publicKey=pair.publicKey.export({format:"der",type:"spki"}).toString("base64");
  const versionRoot=join(root,version);await mkdir(versionRoot);
  const app="CELIKOM-Windows-"+version+".exe",bytes=Buffer.alloc(11000,0x52);
  const data={schema:2,channel:"stable",publisher:"CELIKOM",version,sequence,
    packageUrl:origin+"/CELIKOM/Windows/Updates/stable/"+version+"/"+app,
    packageSize:bytes.length,sha256:sha(bytes),
    publishedAt:new Date(Date.now()-60_000).toISOString(),
    expiresAt:new Date(Date.now()+7*86_400_000).toISOString(),
    minimumVersion:null,mandatory:false,notes:"",rollback:null,
    applicationSha256:"1".repeat(64),nativeHostSha256:"2".repeat(64),
    rendererSha256:"3".repeat(64),supervisorSha256:"4".repeat(64)};
  const doc=Buffer.from(JSON.stringify(data)),signature=sign("sha256",doc,{key:pair.privateKey,dsaEncoding:"der"});
  await Promise.all([
    writeFile(join(versionRoot,app),bytes),
    writeFile(join(versionRoot,"manifest.json"),doc),
    writeFile(join(versionRoot,"manifest.json.sig"),signature),
    writeFile(join(root,"latest.json"),doc),writeFile(join(root,"latest.json.sig"),signature),
    writeFile(join(root,"manifest-public-key.der"),Buffer.from(publicKey,"base64"))
  ]);
  return {root,versionRoot,doc,publicKey,pair,app,data};
}
test("W155 P-256 signed stable release verifies exact immutable/latest pair and package",async t=>{
  const f=await fixture(t);
  const r=await verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  });
  assert.equal(r.sequence,1);assert.equal(r.packageName,f.app);
});
test("W148 tampering with the signed latest JSON fails before any deployment",async t=>{
  const f=await fixture(t);
  await writeFile(join(f.root,"latest.json"),Buffer.from(f.doc.toString().replace('"sequence":1','"sequence":2')));
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  }),/MANIFEST_PAIR_MISMATCH/);
});
test("W155 refuses wrong pinned release identity and wrong domain",async t=>{
  const f=await fixture(t);
  const other=generateKeyPairSync("ec",{namedCurve:"prime256v1"}).publicKey
    .export({format:"der",type:"spki"}).toString("base64");
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:other
  }),/BOUNDS_OR_PUBLIC_KEY_FILE_INVALID/);
  for (const wrongOrigin of ["https://darkred-camel-588676.hostingersite.com",
    "https://updates.celikom.com","https://www.celikom.com"]) {
    await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
      origin:wrongOrigin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
    }),/ORIGIN_INVALID/);
  }
});


test("W155 expired signed release is rejected before publication",async t=>{
  const f=await fixture(t);
  const expired={...f.data,
    publishedAt:"2026-11-01T00:00:00.000Z",
    expiresAt:"2026-11-02T00:00:00.000Z"};
  const doc=Buffer.from(JSON.stringify(expired));
  const signature=sign("sha256",doc,{key:f.pair.privateKey,dsaEncoding:"der"});
  await Promise.all([
    writeFile(join(f.versionRoot,"manifest.json"),doc),
    writeFile(join(f.versionRoot,"manifest.json.sig"),signature),
    writeFile(join(f.root,"latest.json"),doc),
    writeFile(join(f.root,"latest.json.sig"),signature)
  ]);
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  }),/MANIFEST_LIFETIME_INVALID/);
});

test("W155 release public-key sidecar must match the build-pinned P-256 key",async t=>{
  const f=await fixture(t);
  const other=generateKeyPairSync("ec",{namedCurve:"prime256v1"}).publicKey
    .export({format:"der",type:"spki"});
  await writeFile(join(f.root,"manifest-public-key.der"),other);
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  }),/BOUNDS_OR_PUBLIC_KEY_FILE_INVALID/);
});

test("W155 publisher stages beside stable feed so latest promotion is same-filesystem atomic",async()=>{
  const publisher=await readFile(
    new URL("../windows-stable-publish-hostinger.sh",import.meta.url),"utf8");
  assert.ok(publisher.includes('remote_root="$root/CELIKOM/Windows/Updates/stable/.incoming-$GITHUB_RUN_ID"'));
  assert.ok(publisher.includes("W155_RELEASE_STAGE_UNSAFE"));
  assert.ok(publisher.includes('mv -f "$stage/latest.json" "$dest/latest.json"'));
  assert.ok(publisher.includes('mv -f "$stage/latest.json.sig" "$dest/latest.json.sig"'));
});


test("W155 publisher monotonic floor comes only from the exact signed existing latest pair",async t=>{
  const f=await fixture(t);
  const signature=sign("sha256",f.doc,{key:f.pair.privateKey,dsaEncoding:"der"});
  const identity=verifyExistingStableLatest(f.doc,signature,{
    origin,pinnedPublicKeyDerBase64:f.publicKey
  });
  assert.equal(identity.sequence,sequence);
  assert.equal(identity.manifestSha256,sha(f.doc));
  assert.equal(identity.signatureSha256,sha(signature));
  const tampered=Buffer.from(f.doc.toString().replace('"sequence":1','"sequence":2'));
  assert.throws(()=>verifyExistingStableLatest(tampered,signature,{
    origin,pinnedPublicKeyDerBase64:f.publicKey
  }),/SIGNATURE_INVALID/);
});

test("W155 publisher can preserve the sequence floor from an expired but validly signed latest",async t=>{
  const f=await fixture(t);
  const expired={...f.data,
    publishedAt:"2026-11-01T00:00:00.000Z",
    expiresAt:"2026-11-02T00:00:00.000Z"};
  const doc=Buffer.from(JSON.stringify(expired));
  const signature=sign("sha256",doc,{key:f.pair.privateKey,dsaEncoding:"der"});
  const identity=verifyExistingStableLatest(doc,signature,{
    origin,pinnedPublicKeyDerBase64:f.publicKey
  });
  assert.equal(identity.sequence,sequence);
});


test("W155 remote Hostinger promotion block is valid Bash and bound to verified prior bytes",async()=>{
  const publisherPath=new URL("../windows-stable-publish-hostinger.sh",import.meta.url);
  const publisher=await readFile(publisherPath,"utf8");
  assert.ok(publisher.includes("windows-stable-existing-latest.mjs"));
  assert.ok(publisher.includes('|| -L "$dest/latest.json"'));
  assert.ok(publisher.includes('|| -L "$dest/$version/$file"'));
  if(process.platform!=="win32")
    execFileSync("bash",["-n",publisherPath.pathname],{stdio:"pipe"});
  assert.ok(publisher.includes("W155_EXISTING_LATEST_BYTES_CHANGED"));
  assert.ok(publisher.includes("W155_EXISTING_LATEST_CHANGED_DURING_PUBLISH"));
  assert.ok(publisher.includes("-I -H 'Cache-Control: no-cache, no-store'"));
  assert.ok(publisher.includes('"/home/u235811320/domains/celikom.com"'));
  assert.ok(publisher.includes("W155_DEPLOY_ROOT_MISSING_OR_UNSAFE"));
  assert.ok(publisher.includes("W155_GITHUB_RUN_ID_INVALID"));
  const start=publisher.indexOf("<<'REMOTE'\n");
  const end=publisher.indexOf("\nREMOTE",start+10);
  assert.ok(start>=0&&end>start);
  const remote=publisher.slice(start+"<<'REMOTE'\n".length,end);
  if(process.platform!=="win32")
    execFileSync("bash",["-n"],{input:remote,stdio:["pipe","pipe","pipe"]});
});


test("W155 oversized release package is rejected from file metadata before hashing",async t=>{
  const f=await fixture(t);
  await truncate(join(f.versionRoot,f.app),125_000_001);
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  }),/PACKAGE_FILE_INVALID/);
});

test("W155 release verifier rejects a symlinked installer package",async t=>{
  if(process.platform==="win32")return t.skip("Windows symlink creation is privilege-dependent");
  const f=await fixture(t);
  const packagePath=join(f.versionRoot,f.app);
  const outside=join(f.root,"outside.exe");
  await writeFile(outside,Buffer.alloc(11000,0x52));
  await rm(packagePath);
  await symlink(outside,packagePath);
  await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
    origin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
  }),/PACKAGE_FILE_INVALID/);
});


test("W155 local publisher rehearsal promotes a signed release and rejects a changed prior feed",async t=>{
  if(process.platform==="win32")return t.skip("The remote publisher rehearsal uses POSIX sha256sum and Bash");
  const f=await fixture(t);
  const publisher=await readFile(
    new URL("../windows-stable-publish-hostinger.sh",import.meta.url),"utf8");
  const start=publisher.indexOf("<<'REMOTE'\n");
  const end=publisher.indexOf("\nREMOTE",start+10);
  assert.ok(start>=0&&end>start);
  let remote=publisher.slice(start+"<<'REMOTE'\n".length,end);
  const testRoot=join(f.root,"local-deploy-root");
  await mkdir(testRoot);
  for(const path of [
    "/home","/home/u235811320","/home/u235811320/domains",
    "/home/u235811320/domains/celikom.com"
  ])remote=remote.replaceAll('"'+path+'"',JSON.stringify(testRoot));

  async function makeStage(stage,app,bytes,doc,signature){
    await mkdir(stage);
    await Promise.all([
      writeFile(join(stage,app),bytes),
      writeFile(join(stage,"manifest.json"),doc),
      writeFile(join(stage,"manifest.json.sig"),signature),
      writeFile(join(stage,"latest.json"),doc),
      writeFile(join(stage,"latest.json.sig"),signature)
    ]);
    const sums=execFileSync("sha256sum",[
      app,"manifest.json","manifest.json.sig","latest.json","latest.json.sig"
    ],{cwd:stage,encoding:"utf8"});
    await writeFile(join(stage,"SHA256SUMS.txt"),sums);
  }
  function runRemote(stage,releaseVersion,releaseSequence,app,oldSequence,oldManifestSha,oldSignatureSha){
    return execFileSync("bash",["-s","--",testRoot,stage,releaseVersion,
      String(releaseSequence),app,String(oldSequence),oldManifestSha,oldSignatureSha],
      {input:remote,encoding:"utf8"});
  }

  const firstBytes=await readFile(join(f.versionRoot,f.app));
  const firstDoc=Buffer.from(JSON.stringify(f.data,null,2));
  const firstSignature=sign("sha256",firstDoc,{key:f.pair.privateKey,dsaEncoding:"der"});
  const firstStage=join(f.root,"stage-first");
  await makeStage(firstStage,f.app,firstBytes,firstDoc,firstSignature);
  const zero="0".repeat(64);
  assert.match(runRemote(firstStage,version,sequence,f.app,0,zero,zero),
    /W155_SIGNED_STABLE_REMOTE_PUBLISHED/);

  const dest=join(testRoot,"CELIKOM","Windows","Updates","stable");
  assert.deepEqual(await readFile(join(dest,"latest.json")),firstDoc);
  assert.deepEqual(await readFile(join(dest,version,f.app)),firstBytes);
  const priorManifestSha=sha(firstDoc),priorSignatureSha=sha(firstSignature);

  const nextVersion="0.24.39",nextApp="CELIKOM-Windows-"+nextVersion+".exe";
  const nextBytes=Buffer.alloc(12000,0x53);
  const nextData={...f.data,version:nextVersion,sequence:2,
    packageUrl:origin+"/CELIKOM/Windows/Updates/stable/"+nextVersion+"/"+nextApp,
    packageSize:nextBytes.length,sha256:sha(nextBytes),
    publishedAt:new Date(Date.now()-30_000).toISOString(),
    expiresAt:new Date(Date.now()+7*86_400_000).toISOString()};
  const nextDoc=Buffer.from(JSON.stringify(nextData,null,2));
  const nextSignature=sign("sha256",nextDoc,{key:f.pair.privateKey,dsaEncoding:"der"});
  const nextStage=join(f.root,"stage-next");
  await makeStage(nextStage,nextApp,nextBytes,nextDoc,nextSignature);

  await writeFile(join(dest,"latest.json"),Buffer.concat([firstDoc,Buffer.from("\n")]));
  let changedPriorRejected=false,refusalOutput="";
  try{
    runRemote(nextStage,nextVersion,2,nextApp,1,priorManifestSha,priorSignatureSha);
  }catch(error){
    refusalOutput=String(error.stdout)+String(error.stderr)+String(error.message);
    changedPriorRejected=error.status===3&&
      refusalOutput.includes("W155_EXISTING_LATEST_BYTES_CHANGED");
  }
  assert.ok(changedPriorRejected,
    "publisher must refuse a feed changed after its signed preflight; output: "+refusalOutput);

  await writeFile(join(dest,"latest.json"),firstDoc);
  assert.match(runRemote(nextStage,nextVersion,2,nextApp,1,priorManifestSha,priorSignatureSha),
    /W155_SIGNED_STABLE_REMOTE_PUBLISHED/);
  assert.deepEqual(await readFile(join(dest,"latest.json")),nextDoc);
  assert.deepEqual(await readFile(join(dest,nextVersion,nextApp)),nextBytes);
});
