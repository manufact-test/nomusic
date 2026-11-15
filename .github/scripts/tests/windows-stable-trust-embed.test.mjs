import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync} from "node:crypto";
import {renderStableTrustSource} from "../windows-stable-trust-embed.mjs";

const key=generateKeyPairSync("ec",{namedCurve:"prime256v1"}).publicKey
  .export({format:"der",type:"spki"}).toString("base64");
const original=['private const string ProductionFeedOrigin = "";',
 'private const string ProductionManifestPublicKeyDerBase64 = "";'].join("\n");
const valid={origin:"https://celikom.com",publicKeyDerBase64:key};

test("W155 release build embeds only the fixed origin and public P-256 key",()=>{
  const result=renderStableTrustSource(original,valid);
  assert.ok(result.includes('ProductionFeedOrigin = "https://celikom.com/";'));
  assert.ok(result.includes('ProductionManifestPublicKeyDerBase64 = "'+key+'";'));
  assert.equal((result.match(/private const string Production/g)||[]).length,2);
  assert.ok(!result.includes(' = "";'));
  assert.ok(!result.includes("PRIVATE KEY"));
});
test("W155 source defaults remain fail-closed and cannot be silently re-pinned",()=>{
  assert.throws(()=>renderStableTrustSource(
    renderStableTrustSource(original,valid),valid),/SOURCE_NOT_EMPTY/);
  assert.throws(()=>renderStableTrustSource(original+"\n"+original,valid),/SOURCE_NOT_EMPTY/);
});
test("W155 rejects staging, subdomains, HTTP, ports and path overrides",()=>{
  for(const origin of ["http://celikom.com","https://updates.celikom.com",
    "https://www.celikom.com","https://celikom.example","https://celikom.com:8443",
    "https://celikom.com/subfolder","https://celikom.com@evil.invalid",
    "https://darkred-camel-588676.hostingersite.com"]){
    assert.throws(()=>renderStableTrustSource(original,{...valid,origin}),/ORIGIN_INVALID/,origin);
  }
});
test("W155 rejects non-P256 and malformed public keys",()=>{
  const bad=generateKeyPairSync("ec",{namedCurve:"secp384r1"}).publicKey
    .export({format:"der",type:"spki"}).toString("base64");
  assert.throws(()=>renderStableTrustSource(original,{...valid,publicKeyDerBase64:bad}),/PUBLIC_KEY_NOT_P256/);
  assert.throws(()=>renderStableTrustSource(original,{...valid,publicKeyDerBase64:""}),/PUBLIC_KEY_INVALID/);
});
