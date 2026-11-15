import {createHash,createPublicKey,verify} from "node:crypto";
import {readFile,stat} from "node:fs/promises";
import {join} from "node:path";
import {pathToFileURL} from "node:url";
import {resolve} from "node:path";
function bad(code){throw new Error("W155_STABLE_RELEASE_"+code);}
function sha(bytes){return createHash("sha256").update(bytes).digest("hex");}
const hex64=/^[a-f0-9]{64}$/;
const versionRe=/^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}$/;
/** Fail-closed verification before ANY transfer of a production release. */
export async function verifyPreparedStableRelease(directory,{origin,version,
  sequence,pinnedPublicKeyDerBase64}={}) {
  if(typeof version!=="string" || !versionRe.test(version) ||
     !Number.isSafeInteger(sequence)||sequence<=0)bad("VERSION_OR_SEQUENCE_INVALID");
  let url;
  try{url=new URL(origin);}catch{bad("ORIGIN_INVALID");}
  if(url.protocol!=="https:" || url.hostname!=="celikom.com" ||
     url.username || url.password || url.pathname!=="/" ||
     url.search || url.hash || url.port)bad("ORIGIN_INVALID");
  let publicKey;
  try{
    const key=Buffer.from(pinnedPublicKeyDerBase64,"base64");
    publicKey=createPublicKey({key,format:"der",type:"spki"});
    if(publicKey.asymmetricKeyType!=="ec"||
       publicKey.asymmetricKeyDetails?.namedCurve!=="prime256v1"||
       publicKey.export({format:"der",type:"spki"}).toString("base64")!==pinnedPublicKeyDerBase64)
      bad("KEY_INVALID");
  }catch{bad("KEY_INVALID");}
  const app="CELIKOM-Windows-"+version+".exe";
  const root=resolve(directory),versionRoot=join(root,version);
  const [latest,latestSig,immutable,immutableSig,packageBytes,info]=await Promise.all([
    readFile(join(root,"latest.json")),readFile(join(root,"latest.json.sig")),
    readFile(join(versionRoot,"manifest.json")),readFile(join(versionRoot,"manifest.json.sig")),
    readFile(join(versionRoot,app)),stat(join(versionRoot,app))
  ]);
  if(latest.length>16384||immutable.length>16384||
     latestSig.length<64||latestSig.length>80||
     immutableSig.length<64||immutableSig.length>80||
     info.size<10000||info.size>125000000)bad("BOUNDS_INVALID");
  if(!latest.equals(immutable))bad("MANIFEST_PAIR_MISMATCH");
  if(!verify("sha256",latest,{key:publicKey,dsaEncoding:"der"},latestSig)||
     !verify("sha256",immutable,{key:publicKey,dsaEncoding:"der"},immutableSig))
    bad("SIGNATURE_INVALID");
  let data;
  try{data=JSON.parse(latest.toString("utf8"));}catch{bad("JSON_INVALID");}
  if(data.schema!==2||data.channel!=="stable"||data.publisher!=="CELIKOM"||
     data.version!==version||data.sequence!==sequence||
     data.packageUrl!==url.origin+"/CELIKOM/Windows/Updates/stable/"+version+"/"+app||
     data.packageSize!==info.size||data.sha256!==sha(packageBytes)||
     ![data.applicationSha256,data.nativeHostSha256,data.rendererSha256,
       data.supervisorSha256].every(x=>typeof x==="string"&&hex64.test(x))||
     data.rollback!==null)bad("MANIFEST_POLICY_INVALID");
  return {version,sequence,packageName:app,packageSha256:data.sha256,
    manifestSha256:sha(immutable),signatureSha256:sha(immutableSig)};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  if(process.argv.length!==5)bad("ARGS_INVALID");
  const res=await verifyPreparedStableRelease(process.argv[2],{
    version:process.argv[3],sequence:Number(process.argv[4]),
    origin:process.env.CELIKOM_STABLE_ORIGIN,
    pinnedPublicKeyDerBase64:process.env.CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
  });
  console.log("W155_STABLE_RELEASE_VERIFIED version="+res.version+
    " sequence="+res.sequence+" package_sha256="+res.packageSha256);
}
