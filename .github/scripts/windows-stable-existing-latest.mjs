import {createHash,createPublicKey,verify} from "node:crypto";
import {readFile} from "node:fs/promises";
import {pathToFileURL} from "node:url";
import {resolve} from "node:path";

const versionRe=/^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}$/;
const hex64=/^[a-f0-9]{64}$/;
function fail(code){throw new Error("W155_EXISTING_LATEST_"+code);}
function sha(bytes){return createHash("sha256").update(bytes).digest("hex");}

/** Verify the currently served latest pair before using its sequence as the
 * publisher's monotonic floor. Expiry is allowed here: an old, expired but
 * correctly signed manifest still proves the last sequence that was issued.
 */
export function verifyExistingStableLatest(manifest,signature,{
  origin,pinnedPublicKeyDerBase64
}={}){
  if(!Buffer.isBuffer(manifest)||manifest.length<1||manifest.length>16384||
     !Buffer.isBuffer(signature)||signature.length<64||signature.length>80)
    fail("BOUNDS_INVALID");
  let url;
  try{url=new URL(origin);}catch{fail("ORIGIN_INVALID");}
  if(url.protocol!=="https:"||url.hostname!=="celikom.com"||
     url.username||url.password||url.pathname!=="/"||url.search||url.hash||url.port)
    fail("ORIGIN_INVALID");
  let publicKey;
  try{
    const key=Buffer.from(pinnedPublicKeyDerBase64,"base64");
    publicKey=createPublicKey({key,format:"der",type:"spki"});
    if(publicKey.asymmetricKeyType!=="ec"||
       publicKey.asymmetricKeyDetails?.namedCurve!=="prime256v1"||
       publicKey.export({format:"der",type:"spki"}).toString("base64")!==pinnedPublicKeyDerBase64)
      fail("KEY_INVALID");
  }catch{fail("KEY_INVALID");}
  if(!verify("sha256",manifest,{key:publicKey,dsaEncoding:"der"},signature))
    fail("SIGNATURE_INVALID");
  let data;
  try{data=JSON.parse(manifest.toString("utf8"));}catch{fail("JSON_INVALID");}
  if(!data||typeof data!=="object"||Array.isArray(data))fail("JSON_INVALID");
  const published=typeof data.publishedAt==="string"&&data.publishedAt.endsWith("Z")
    ?Date.parse(data.publishedAt):NaN;
  const expires=typeof data.expiresAt==="string"&&data.expiresAt.endsWith("Z")
    ?Date.parse(data.expiresAt):NaN;
  const now=Date.now();
  if(!Number.isFinite(published)||!Number.isFinite(expires)||
     new Date(published).toISOString()!==data.publishedAt||
     new Date(expires).toISOString()!==data.expiresAt||
     published>now+5*60_000||expires<=published||
     expires>published+30*86_400_000)
    fail("MANIFEST_LIFETIME_INVALID");
  const version=data.version;
  const app="CELIKOM-Windows-"+version+".exe";
  if(data.schema!==2||data.channel!=="stable"||data.publisher!=="CELIKOM"||
     typeof version!=="string"||!versionRe.test(version)||
     !Number.isSafeInteger(data.sequence)||data.sequence<=0||
     data.packageUrl!==url.origin+"/CELIKOM/Windows/Updates/stable/"+version+"/"+app||
     !Number.isSafeInteger(data.packageSize)||data.packageSize<10000||
     data.packageSize>125000000||!hex64.test(data.sha256??"")||
     ![data.applicationSha256,data.nativeHostSha256,data.rendererSha256,
       data.supervisorSha256].every(x=>typeof x==="string"&&hex64.test(x))||
     typeof data.mandatory!=="boolean"||typeof data.notes!=="string"||
     data.notes.length>240||
     data.minimumVersion!==null&&
       (typeof data.minimumVersion!=="string"||!versionRe.test(data.minimumVersion)))
    fail("MANIFEST_POLICY_INVALID");
  return {sequence:data.sequence,manifestSha256:sha(manifest),
    signatureSha256:sha(signature)};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  if(process.argv.length!==4)fail("ARGS_INVALID");
  const manifest=await readFile(process.argv[2]);
  const signature=await readFile(process.argv[3]);
  const identity=verifyExistingStableLatest(manifest,signature,{
    origin:process.env.CELIKOM_STABLE_ORIGIN,
    pinnedPublicKeyDerBase64:process.env.CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
  });
  console.log([identity.sequence,identity.manifestSha256,identity.signatureSha256].join(" "));
}
