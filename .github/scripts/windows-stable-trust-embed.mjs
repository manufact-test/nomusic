import {createPublicKey} from "node:crypto";
import {readFile, writeFile} from "node:fs/promises";
import {pathToFileURL} from "node:url";
import {resolve} from "node:path";

const fields = {
  ProductionFeedOrigin: "origin",
  ProductionManifestPublicKeyDerBase64: "publicKeyDerBase64"
};
function invalid(message) { throw new Error("W155_" + message); }

/**
 * Release-only operation: embed the fixed production origin and PUBLIC P-256
 * key in the GUI/Supervisor. Never reads or stores a signing private key.
 * Checked-in defaults remain fail-closed until the final bootstrap is built.
 */
export function renderStableTrustSource(source, values) {
  const {origin, publicKeyDerBase64} = values || {};
  let url;
  try { url = new URL(origin); } catch { invalid("ORIGIN_INVALID"); }
  if (url.protocol !== "https:" || url.hostname !== "celikom.com" ||
      url.username || url.password || url.pathname !== "/" ||
      url.search || url.hash || url.port !== "")
    invalid("ORIGIN_INVALID");
  if (typeof publicKeyDerBase64 !== "string" ||
      !/^[A-Za-z0-9+/]+={0,2}$/.test(publicKeyDerBase64))
    invalid("PUBLIC_KEY_INVALID");
  let key;
  try {
    key = createPublicKey({key:Buffer.from(publicKeyDerBase64,"base64"),
      format:"der", type:"spki"});
  } catch { invalid("PUBLIC_KEY_INVALID"); }
  if (key.asymmetricKeyType !== "ec" ||
      key.asymmetricKeyDetails?.namedCurve !== "prime256v1" ||
      key.export({format:"der",type:"spki"}).toString("base64") !== publicKeyDerBase64)
    invalid("PUBLIC_KEY_NOT_P256");
  if (typeof source !== "string") invalid("SOURCE_INVALID");

  let output=source;
  const replacements={origin:url.origin+"/",publicKeyDerBase64};
  for (const [field,parameter] of Object.entries(fields)) {
    const oldText = 'private const string ' + field + ' = "";';
    if (output.split(oldText).length !== 2) invalid("SOURCE_NOT_EMPTY_" + field);
    output=output.replace(oldText,
      'private const string ' + field + ' = ' + JSON.stringify(replacements[parameter]) + ';');
  }
  return output;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const srcPath = process.argv[2];
  if (!srcPath || process.argv.length !== 3)
    invalid("SOURCE_PATH_REQUIRED");
  const source=await readFile(srcPath,"utf8");
  const transformed=renderStableTrustSource(source,{
    origin:process.env.CELIKOM_STABLE_ORIGIN,
    publicKeyDerBase64:process.env.CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64
  });
  await writeFile(srcPath,transformed,{encoding:"utf8"});
  console.log("W155_P256_PUBLIC_TRUST_PINS_EMBEDDED");
}
