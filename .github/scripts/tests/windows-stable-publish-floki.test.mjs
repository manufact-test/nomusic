import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync,sign,createHash} from "node:crypto";
import {mkdtemp,mkdir,writeFile,readFile,readlink,rm,symlink,readdir} from "node:fs/promises";
import {join} from "node:path";
import {tmpdir} from "node:os";
import {promoteLocalFeed} from "../windows-stable-publish-floki.mjs";
const origin="https://celikom.com";
const sha=x=>createHash("sha256").update(x).digest("hex");
test("Floki local feed promotion preserves immutable versions and signed monotonic pointer",async t=>{
  if(process.platform==="win32") return t.skip("Linux-only publisher");
  const dir=await mkdtemp(join(tmpdir(),"floki-feed-")); t.after(()=>rm(dir,{recursive:true,force:true}));
  const root=join(dir,"stable"); await mkdir(root,{mode:0o755});
  const pair=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  const pinnedPublicKeyDerBase64=pair.publicKey.export({format:"der",type:"spki"}).toString("base64");
  async function fixture(name,version,sequence){
    const source=join(dir,name); await mkdir(source,{mode:0o700}); await mkdir(join(source,version),{mode:0o700});
    const app="CELIKOM-Windows-"+version+".exe",bytes=Buffer.alloc(11000,sequence);
    const data={schema:2,channel:"stable",publisher:"CELIKOM",version,sequence,
      packageUrl:origin+"/CELIKOM/Windows/Updates/stable/"+version+"/"+app,
      packageSize:bytes.length,sha256:sha(bytes),publishedAt:new Date(Date.now()-60000).toISOString(),
      expiresAt:new Date(Date.now()+86400000).toISOString(),minimumVersion:null,mandatory:false,notes:"",rollback:null,
      applicationSha256:"1".repeat(64),nativeHostSha256:"2".repeat(64),rendererSha256:"3".repeat(64),supervisorSha256:"4".repeat(64)};
    const doc=Buffer.from(JSON.stringify(data)),sig=sign("sha256",doc,{key:pair.privateKey,dsaEncoding:"der"});
    for(const [file,value] of [["latest.json",doc],["latest.json.sig",sig],["manifest-public-key.der",Buffer.from(pinnedPublicKeyDerBase64,"base64")],[version+"/manifest.json",doc],[version+"/manifest.json.sig",sig],[version+"/"+app,bytes]]) await writeFile(join(source,file),value,{mode:0o600});
    return {source,root,version,sequence,pinnedPublicKeyDerBase64,doc,app,bytes};
  }
  const first=await fixture("first","0.24.54",1);
  await promoteLocalFeed(first);
  assert.equal(await readlink(join(root,"current")),"versions/0.24.54");
  assert.deepEqual(await readFile(join(root,"current","manifest.json")),first.doc);
  const next=await fixture("next","0.24.55",2);
  await assert.rejects(()=>promoteLocalFeed({...next,pinnedPublicKeyDerBase64:"invalid"}));
  assert.equal(await readlink(join(root,"current")),"versions/0.24.54");
  const corrupt=await fixture("corrupt","0.24.55",2);
  await writeFile(join(corrupt.source,corrupt.version,corrupt.app),Buffer.alloc(11000,0));
  await assert.rejects(()=>promoteLocalFeed(corrupt),/MANIFEST_POLICY_INVALID/);
  const link=await fixture("link","0.24.55",2);
  await rm(join(link.source,link.version,link.app)); await symlink(join(next.source,next.version,next.app),join(link.source,link.version,link.app));
  await assert.rejects(()=>promoteLocalFeed(link),/UNSAFE_FILE/);
  const downgrade=await fixture("downgrade","0.24.53",3);
  await assert.rejects(()=>promoteLocalFeed(downgrade),/NON_MONOTONIC/);
  const replay=await fixture("replay","0.24.55",1);
  await assert.rejects(()=>promoteLocalFeed(replay),/NON_MONOTONIC/);
  await promoteLocalFeed(next);
  assert.equal(await readlink(join(root,"current")),"versions/0.24.55");
  assert.deepEqual(await readFile(join(root,"versions",first.version,first.app)),first.bytes);
  assert.deepEqual((await readdir(join(root,"current"))).sort(),[next.app,"manifest.json","manifest.json.sig"].sort());
  await rm(join(root,"current"));
  const third=await fixture("third","0.24.56",3);
  await assert.rejects(()=>promoteLocalFeed(third),/MISSING_CURRENT/);
});
