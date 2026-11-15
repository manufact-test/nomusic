import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,mkdir,readFile,lstat,rm} from "node:fs/promises";
import {createPublicKey} from "node:crypto";
import {join} from "node:path";
import {tmpdir} from "node:os";
import {createOfflineStableManifestKeypair} from "../windows-stable-keygen.mjs";

test("W155 offline P256 generator never prints or commits a private key",async t=>{
 const root=await mkdtemp(join(tmpdir(),"celikom-keygen-"));
 t.after(()=>rm(root,{recursive:true,force:true}));
 const dir=join(root,"fresh");
 const result=await createOfflineStableManifestKeypair(dir);
 const pem=await readFile(join(dir,"manifest-private.pem"),"utf8");
 const der=await readFile(join(dir,"manifest-public.der"));
 const pub=(await readFile(join(dir,"manifest-public-base64.txt"),"utf8")).trim();
 assert.ok(pem.includes("BEGIN PRIVATE KEY"));
 assert.equal(der.toString("base64"),pub);
 const parsed=createPublicKey({key:der,type:"spki",format:"der"});
 assert.equal(parsed.asymmetricKeyDetails.namedCurve,"prime256v1");
 assert.ok(/^[a-f0-9]{64}$/.test(result.publicSha256));
 if(process.platform!=="win32") {
   assert.equal((await lstat(join(dir,"manifest-private.pem"))).mode&0o077,0);
 }
 await assert.rejects(()=>createOfflineStableManifestKeypair(dir),/EEXIST/);
});
