import {generateKeyPairSync,createHash} from "node:crypto";
import {mkdir,writeFile,lstat} from "node:fs/promises";
import {resolve,join} from "node:path";
import {pathToFileURL} from "node:url";

/** Generate the one offline production signing keypair without printing
 * the PRIVATE key into logs, chat or an artifact. Run only on a trusted
 * release-operator machine and add private PEM to protected GitHub secrets.
 */
export async function createOfflineStableManifestKeypair(output) {
  if(typeof output!=="string" || !output.trim()) throw Error("W155_KEY_DIR_MISSING");
  const dir=resolve(output);
  await mkdir(dir,{mode:0o700});
  const status=await lstat(dir);
  if(!status.isDirectory()||status.isSymbolicLink())throw Error("W155_KEY_DIR_UNSAFE");
  const {privateKey,publicKey}=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  const privatePem=privateKey.export({type:"pkcs8",format:"pem"});
  const der=publicKey.export({type:"spki",format:"der"});
  await writeFile(join(dir,"manifest-private.pem"),privatePem,{mode:0o600,flag:"wx"});
  await writeFile(join(dir,"manifest-public.der"),der,{mode:0o600,flag:"wx"});
  await writeFile(join(dir,"manifest-public-base64.txt"),der.toString("base64")+"\n",
    {mode:0o600,flag:"wx"});
  return {directory:dir,publicSha256:createHash("sha256").update(der).digest("hex")};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  if(process.argv.length!==3)throw Error("W155_EXPECT_OUTPUT_DIRECTORY");
  const result=await createOfflineStableManifestKeypair(process.argv[2]);
  console.log("W155_OFFLINE_P256_KEYPAIR_CREATED public_sha256="+result.publicSha256);
  console.log("W155_PRIVATE_KEY_STAYS_ON_OPERATOR_MACHINE_NOT_IN_REPOSITORY");
}
