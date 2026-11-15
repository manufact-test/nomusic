import test from "node:test";
import assert from "node:assert/strict";
import {generateKeyPairSync} from "node:crypto";
import {renderStableTrustSource} from "../windows-stable-trust-embed.mjs";

const key=generateKeyPairSync("ec",{namedCurve:"prime256v1"}).publicKey
  .export({format:"der",type:"spki"}).toString("base64");
const original=['private const string ProductionFeedOrigin = "";',
 'private const string ProductionManifestPublicKeyDerBase64 = "";',
 'private const string ProductionSignerCertificateSha256 = "";'].join("\n");
const valid={origin:"https://updates.celikom.com",publicKeyDerBase64:key,
  signerSha256:"A".repeat(64)};

test("W148 production build embeds only public trust identifiers, never private keys",()=>{
  const result=renderStableTrustSource(original,valid);
  assert.ok(result.includes('ProductionFeedOrigin = "https://updates.celikom.com/";'));
  assert.ok(result.includes('ProductionManifestPublicKeyDerBase64 = "'+key+'";'));
  assert.ok(result.includes('ProductionSignerCertificateSha256 = "'+"a".repeat(64)+'";'));
  assert.equal((result.match(/private const string Production/g)||[]).length,3);
  assert.ok(!result.includes(' = "";'));
});
test("W148 source defaults remain fail-closed and cannot be silently re-pinned",()=>{
  assert.throws(()=>renderStableTrustSource(
    renderStableTrustSource(original,valid),valid),/SOURCE_NOT_EMPTY/);
  assert.throws(()=>renderStableTrustSource(original+"\n"+original,valid),/SOURCE_NOT_EMPTY/);
});
test("W148 cannot trust staging host, HTTP, ports or path overrides",()=>{
  for(const origin of ["http://celikom.com","https://celikom.example",
    "https://celikom.com:8443","https://celikom.com/subfolder",
    "https://celikom.com@evil.invalid","https://darkred-camel-588676.hostingersite.com"]){
    assert.throws(()=>renderStableTrustSource(original,{...valid,origin}),/ORIGIN_INVALID/,origin);
  }
});
test("W148 rejects non-P256 and missing certificate fingerprint",()=>{
  const bad=generateKeyPairSync("ec",{namedCurve:"secp384r1"}).publicKey
    .export({format:"der",type:"spki"}).toString("base64");
  assert.throws(()=>renderStableTrustSource(original,{...valid,publicKeyDerBase64:bad}),/PUBLIC_KEY_NOT_P256/);
  assert.throws(()=>renderStableTrustSource(original,{...valid,signerSha256:""}),/SIGNER_INVALID/);
});
