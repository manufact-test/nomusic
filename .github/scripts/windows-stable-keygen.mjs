import {generateKeyPairSync,createHash} from "node:crypto";
import {mkdir,writeFile,lstat,readdir} from "node:fs/promises";
import {resolve,join} from "node:path";
import {pathToFileURL} from "node:url";

/** Generate the one offline production signing keypair without printing
 * the PRIVATE key into logs, chat or an artifact. Run only on a trusted
 * release-operator machine and add private PEM to protected GitHub secrets.
 */
export async function createOfflineStableManifestKeypair(output) {
  if(typeof output!=="string" || !output.trim()) throw Error("W155_KEY_DIR_MISSING");
  const dir=resolve(output);
  await mkdir(dir,{mode:0o700}).catch(error=>{
    if(error?.code!=="EEXIST")throw error;
  });
  const status=await lstat(dir);
  if(!status.isDirectory()||status.isSymbolicLink())throw Error("W155_KEY_DIR_UNSAFE");
  if((await readdir(dir)).length!==0)throw Error("W155_KEY_DIR_NOT_EMPTY");
  const {privateKey,publicKey}=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  let privatePem=privateKey.export({type:"pkcs8",format:"pem"});
  const privateBytes=Buffer.from(privatePem,"utf8");
  privatePem="";
  const der=publicKey.export({type:"spki",format:"der"});
  const names=["manifest-private.pem","manifest-public.der","manifest-public-base64.txt"];
  const values=[privateBytes,der,Buffer.from(der.toString("base64")+"\n","utf8")];
  const temporary=names.map(name=>join(dir,name+".tmp-"+process.pid));
  const created=[];
  try {
    for(let i=0;i<names.length;i++)
      await writeFile(temporary[i],values[i],{mode:0o600,flag:"wx"});
    for(let i=0;i<names.length;i++){
      const finalPath=join(dir,names[i]);
      await rename(temporary[i],finalPath);
      created.push(finalPath);
    }
    return {directory:dir,publicSha256:createHash("sha256").update(der).digest("hex")};
  } catch(error) {
    await Promise.all([...temporary,...created].map(file=>rm(file,{force:true}).catch(()=>{})));
    throw error;
  } finally {
    privateBytes.fill(0);
    values[2].fill(0);
  }
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  if(process.argv.length!==3)throw Error("W155_EXPECT_OUTPUT_DIRECTORY");
  const result=await createOfflineStableManifestKeypair(process.argv[2]);
  console.log("W155_OFFLINE_P256_KEYPAIR_CREATED public_sha256="+result.publicSha256);
  console.log("W155_PRIVATE_KEY_STAYS_ON_OPERATOR_MACHINE_NOT_IN_REPOSITORY");
}
