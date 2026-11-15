import {createHash,createPrivateKey,createPublicKey} from "node:crypto";
import {appendFileSync,readFileSync} from "node:fs";

export function deriveP256PublicKey(privatePem) {
  if (typeof privatePem !== "string" || !privatePem.includes("BEGIN PRIVATE KEY"))
    throw new Error("W155_PRIVATE_KEY_PEM_INVALID");
  let privateKey;
  try { privateKey=createPrivateKey(privatePem); }
  catch { throw new Error("W155_PRIVATE_KEY_PEM_INVALID"); }
  if (privateKey.asymmetricKeyType !== "ec" ||
      privateKey.asymmetricKeyDetails?.namedCurve !== "prime256v1")
    throw new Error("W155_PRIVATE_KEY_NOT_P256");
  const publicKey=createPublicKey(privateKey);
  const der=publicKey.export({format:"der",type:"spki"});
  const checked=createPublicKey({key:der,format:"der",type:"spki"});
  if (checked.asymmetricKeyType !== "ec" ||
      checked.asymmetricKeyDetails?.namedCurve !== "prime256v1")
    throw new Error("W155_DERIVED_PUBLIC_KEY_NOT_P256");
  return {
    publicKeyDer:der,
    publicKeyDerBase64:der.toString("base64"),
    fingerprint:createHash("sha256").update(der).digest("hex")
  };
}

import {pathToFileURL} from "node:url";
import {resolve} from "node:path";

const isMain=process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href;
if (isMain && process.argv[2] === "--verify-file") {
  const privatePath=process.argv[3];
  const publicPath=process.argv[4];
  if (!privatePath || !publicPath || process.argv.length !== 5)
    throw new Error("W155_VERIFY_FILE_ARGUMENTS_INVALID");
  const result=deriveP256PublicKey(readFileSync(privatePath,"utf8"));
  const stored=readFileSync(publicPath);
  if (!stored.equals(result.publicKeyDer))
    throw new Error("W155_LOCAL_KEYPAIR_PUBLIC_MISMATCH");
  process.stdout.write("W155_P256_LOCAL_KEYPAIR_VERIFY_PASS fingerprint="+result.fingerprint+"\n");
} else if (isMain) {
  const result=deriveP256PublicKey(process.env.MANIFEST_PRIVATE_PEM);
  if (!process.env.GITHUB_ENV || !process.env.GITHUB_OUTPUT)
    throw new Error("W155_GITHUB_WORKFLOW_OUTPUTS_REQUIRED");
  appendFileSync(process.env.GITHUB_ENV,
    "CELIKOM_STABLE_ORIGIN=https://celikom.com\n"+
    "CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64="+result.publicKeyDerBase64+"\n");
  appendFileSync(process.env.GITHUB_OUTPUT,
    "public_key_der_base64="+result.publicKeyDerBase64+"\n");
  process.stdout.write("W155_P256_PUBLIC_PIN_DERIVED_FROM_PROTECTED_KEY fingerprint="+result.fingerprint+"\n");
}
