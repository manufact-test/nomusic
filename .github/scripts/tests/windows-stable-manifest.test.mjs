import test from "node:test";
import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, verify as verifyBytes } from "node:crypto";
import { mkdtemp, writeFile, readFile, rm, symlink } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  buildStableManifestArtifacts, writeStableManifestArtifacts
} from "../windows-stable-manifest.mjs";

const now = new Date();
const publishedAt = now.toISOString();
const expiresAt = new Date(now.getTime() + 7 * 86_400_000).toISOString();
const origin = "https://darkred-camel-588676.hostingersite.com";
const version = "0.24.37";

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), "celikom-w113-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const paths = {
    packagePath: join(root, "CELIKOM-Windows-" + version + ".exe"),
    applicationPath: join(root, "CELIKOM.Companion.exe"),
    nativeHostPath: join(root, "host.cjs"),
    rendererPath: join(root, "renderer.js"),
    supervisorPath: join(root, "CELIKOM.UpdateSupervisor.exe")
  };
  await Promise.all([
    writeFile(paths.packagePath, Buffer.alloc(32_000, 0x51)),
    writeFile(paths.applicationPath, Buffer.alloc(24_000, 0x52)),
    writeFile(paths.nativeHostPath, Buffer.from("module.exports = true;")),
    writeFile(paths.rendererPath, Buffer.from("globalThis.celikom = true;")),
    writeFile(paths.supervisorPath, Buffer.alloc(28_000, 0x53))
  ]);
  const pair = generateKeyPairSync("ec", { namedCurve: "prime256v1" });
  return {
    root, paths,
    signingPrivateKeyPem: pair.privateKey.export({ type: "pkcs8", format: "pem" }),
    expectedPublicKeyDer: pair.publicKey.export({ type: "spki", format: "der" })
  };
}
const hash = bytes => createHash("sha256").update(bytes).digest("hex");

test("W113 creates exact schema-2 manifest and P-256 DER signature for installed payload", async t => {
  const f = await fixture(t);
  const result = await buildStableManifestArtifacts({
    ...f.paths, version, sequence: 17, origin,
    signingPrivateKeyPem: f.signingPrivateKeyPem,
    expectedPublicKeyDer: f.expectedPublicKeyDer, publishedAt, expiresAt,
    notes: "Verified release"
  });
  assert.equal(result.manifest.schema, 2);
  assert.equal(result.manifest.channel, "stable");
  assert.equal(result.manifest.publisher, "CELIKOM");
  assert.equal(result.manifest.sequence, 17);
  assert.equal(result.manifest.packageUrl,
    origin + "/CELIKOM/Windows/Updates/stable/" + version +
    "/CELIKOM-Windows-" + version + ".exe");
  assert.equal(result.manifest.sha256, hash(await readFile(f.paths.packagePath)));
  assert.equal(result.manifest.applicationSha256,
    hash(await readFile(f.paths.applicationPath)));
  assert.equal(result.manifest.nativeHostSha256, hash(await readFile(f.paths.nativeHostPath)));
  assert.equal(result.manifest.rendererSha256, hash(await readFile(f.paths.rendererPath)));
  assert.equal(result.manifest.supervisorSha256, hash(await readFile(f.paths.supervisorPath)));
  assert.equal(result.signature.length >= 64 && result.signature.length <= 80, true);
  assert.equal(verifyBytes("sha256", result.document, {
    key: f.expectedPublicKeyDer, format: "der", type: "spki", dsaEncoding: "der"
  }, result.signature), true);

  const output = join(f.root, "stable-feed");
  await writeStableManifestArtifacts(output, result);
  const versionManifest = join(output, version, "manifest.json");
  const versionSignature = join(output, version, "manifest.json.sig");
  assert.deepEqual(await readFile(versionManifest), result.document);
  assert.equal(verifyBytes("sha256", await readFile(versionManifest), {
    key: f.expectedPublicKeyDer, format: "der", type: "spki", dsaEncoding: "der"
  }, await readFile(versionSignature)), true);
  assert.deepEqual(await readFile(join(output, "latest.json")), result.document);

  // ECDSA signatures may be randomized. An existing immutable version record
  // is reusable only when its document is identical and its old signature is valid.
  await writeStableManifestArtifacts(output, result);
  const changedDocument = Buffer.from(result.document.toString("utf8").replace(
    '"notes": "Verified release"', '"notes": "Changed release"'));
  await assert.rejects(() => writeStableManifestArtifacts(output, {
    ...result, document: changedDocument
  }), /W113_VERSIONED_RELEASE_IMMUTABLE/);
});

test("W113 signature is bound to exact JSON bytes", async t => {
  const f = await fixture(t);
  const result = await buildStableManifestArtifacts({
    ...f.paths, version, sequence: 18, origin,
    signingPrivateKeyPem: f.signingPrivateKeyPem,
    expectedPublicKeyDer: f.expectedPublicKeyDer, publishedAt, expiresAt
  });
  const changed = Buffer.from(result.document.toString("utf8").replace(
    '"mandatory": false', '"mandatory": true'));
  assert.notDeepEqual(changed, result.document);
  assert.equal(verifyBytes("sha256", changed, {
    key: f.expectedPublicKeyDer, format: "der", type: "spki", dsaEncoding: "der"
  }, result.signature), false);
});

test("W113 refuses a private key that does not match the client-pinned public key", async t => {
  const f = await fixture(t);
  const other = generateKeyPairSync("ec", { namedCurve: "prime256v1" });
  await assert.rejects(() => buildStableManifestArtifacts({
    ...f.paths, version, sequence: 19, origin,
    signingPrivateKeyPem: f.signingPrivateKeyPem,
    expectedPublicKeyDer: other.publicKey.export({ type: "spki", format: "der" }),
    publishedAt, expiresAt
  }), /W113_SIGNING_KEY_DOES_NOT_MATCH_PINNED_PUBLIC_KEY/);
});

test("W113 rejects non-P256 keys, malformed origin, version and sequence", async t => {
  const f = await fixture(t);
  const p384 = generateKeyPairSync("ec", { namedCurve: "secp384r1" });
  const common = {
    ...f.paths, version, sequence: 20, origin,
    expectedPublicKeyDer: f.expectedPublicKeyDer, publishedAt, expiresAt
  };
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common,
    signingPrivateKeyPem: p384.privateKey.export({ type: "pkcs8", format: "pem" })
  }), /W113_SIGNING_KEY_NOT_P256/);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, origin: "http://example.com",
    signingPrivateKeyPem: f.signingPrivateKeyPem
  }), /W113_OFFICIAL_ORIGIN_INVALID/);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, version: "../0.24.37",
    signingPrivateKeyPem: f.signingPrivateKeyPem
  }), /W113_VERSION_INVALID/);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, sequence: 0,
    signingPrivateKeyPem: f.signingPrivateKeyPem
  }), /W113_SEQUENCE_INVALID/);
});

test("W113 rejects invalid expiry, package layout and missing trust pin", async t => {
  const f = await fixture(t);
  const common = {
    ...f.paths, version, sequence: 21, origin,
    signingPrivateKeyPem: f.signingPrivateKeyPem,
    expectedPublicKeyDer: f.expectedPublicKeyDer, publishedAt
  };
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, expiresAt: new Date(now.getTime() + 31 * 86_400_000).toISOString()
  }), /W113_MANIFEST_LIFETIME_INVALID/);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, expiresAt, expectedPublicKeyDer: Buffer.from("untrusted")
  }), /W113_SIGNING_TRUST_NOT_CONFIGURED/);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...common, expiresAt, packagePath: f.paths.applicationPath
  }), /W113_RELEASE_PAYLOAD_LAYOUT_INVALID/);
});

test("W113 rejects symbolic-link payload substitution", async t => {
  const f = await fixture(t);
  const link = join(f.root, "linked-renderer.js");
  await symlink(f.paths.rendererPath, link);
  await assert.rejects(() => buildStableManifestArtifacts({
    ...f.paths, rendererPath: link, version, sequence: 22, origin,
    signingPrivateKeyPem: f.signingPrivateKeyPem,
    expectedPublicKeyDer: f.expectedPublicKeyDer, publishedAt, expiresAt
  }), /W113_RENDERER_FILE_INVALID/);
});
