import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync,sign,createHash} from "node:crypto";
import {mkdtemp,mkdir,writeFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {verifyPreparedStableRelease} from "../windows-stable-release-verify.mjs";
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
    packageSize:bytes.length,sha256:sha(bytes),rollback:null,
    applicationSha256:"1".repeat(64),nativeHostSha256:"2".repeat(64),
    rendererSha256:"3".repeat(64),supervisorSha256:"4".repeat(64)};
  const doc=Buffer.from(JSON.stringify(data)),signature=sign("sha256",doc,{key:pair.privateKey,dsaEncoding:"der"});
  await Promise.all([
    writeFile(join(versionRoot,app),bytes),
    writeFile(join(versionRoot,"manifest.json"),doc),
    writeFile(join(versionRoot,"manifest.json.sig"),signature),
    writeFile(join(root,"latest.json"),doc),writeFile(join(root,"latest.json.sig"),signature)
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
  }),/SIGNATURE_INVALID/);
  for (const wrongOrigin of ["https://darkred-camel-588676.hostingersite.com",
    "https://updates.celikom.com","https://www.celikom.com"]) {
    await assert.rejects(()=>verifyPreparedStableRelease(f.root,{
      origin:wrongOrigin,version,sequence,pinnedPublicKeyDerBase64:f.publicKey
    }),/ORIGIN_INVALID/);
  }
});
