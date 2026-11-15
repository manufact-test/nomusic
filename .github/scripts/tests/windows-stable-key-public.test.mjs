import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync} from "node:crypto";
import {deriveP256PublicKey} from "../windows-stable-key-public.mjs";

test("W155 derives the exact SPKI public pin from the protected P-256 PKCS8 key", () => {
  const pair=generateKeyPairSync("ec",{namedCurve:"prime256v1"});
  const pem=pair.privateKey.export({format:"pem",type:"pkcs8"});
  const result=deriveP256PublicKey(pem);
  const expected=pair.publicKey.export({format:"der",type:"spki"});
  assert.deepEqual(result.publicKeyDer,expected);
  assert.equal(result.publicKeyDerBase64,expected.toString("base64"));
  assert.match(result.fingerprint,/^[a-f0-9]{64}$/);
});

test("W155 refuses malformed and non-P256 private keys", () => {
  const p384=generateKeyPairSync("ec",{namedCurve:"secp384r1"});
  const p384Pem=p384.privateKey.export({format:"pem",type:"pkcs8"});
  assert.throws(()=>deriveP256PublicKey("not a key"),/W155_PRIVATE_KEY_PEM_INVALID/);
  assert.throws(()=>deriveP256PublicKey(p384Pem),/W155_PRIVATE_KEY_NOT_P256/);
});
