import {
  createHash, createPrivateKey, createPublicKey, sign as signBytes, timingSafeEqual
} from "node:crypto";
import { createReadStream } from "node:fs";
import { lstat, mkdir, readFile, writeFile, rename, rm } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const MIN_PACKAGE_BYTES = 10_000;
const MAX_PACKAGE_BYTES = 125_000_000;
const MAX_MANIFEST_BYTES = 16_384;
const VERSION_RE = /^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}$/;

function fail(code) { throw new Error(code); }

function validateOrigin(value) {
  let url;
  try { url = new URL(value); } catch { fail("W113_OFFICIAL_ORIGIN_INVALID"); }
  if (url.protocol !== "https:" || !url.hostname || url.username || url.password ||
      url.pathname !== "/" || url.search || url.hash)
    fail("W113_OFFICIAL_ORIGIN_INVALID");
  return url;
}

function validateUtc(value, code) {
  if (typeof value !== "string" || !value.endsWith("Z")) fail(code);
  const time = Date.parse(value);
  if (!Number.isFinite(time) || new Date(time).toISOString() !== value) fail(code);
  return time;
}

async function hashRegularFile(filePath, code) {
  const fullPath = resolve(filePath);
  let info;
  try { info = await lstat(fullPath); } catch { fail(code); }
  if (!info.isFile() || info.isSymbolicLink() || info.size < 1) fail(code);
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(fullPath)) hash.update(chunk);
  return { path: fullPath, size: info.size, sha256: hash.digest("hex") };
}

/**
 * Produces the exact schema-2 JSON bytes and detached P-256 DER signature
 * consumed by StableUpdateManifestFetcher/Verifier.
 * The private key must come from a protected release environment. The
 * derived public key must exactly match the key pinned into the client.
 */
export async function buildStableManifestArtifacts(options) {
  const {
    packagePath, applicationPath, nativeHostPath, rendererPath, version,
    sequence, origin: originText, signingPrivateKeyPem, expectedPublicKeyDer,
    publishedAt = new Date().toISOString(), expiresAt, mandatory = false, notes = ""
  } = options ?? {};

  if (typeof version !== "string" || !VERSION_RE.test(version)) fail("W113_VERSION_INVALID");
  if (!Number.isSafeInteger(sequence) || sequence < 1) fail("W113_SEQUENCE_INVALID");
  if (typeof mandatory !== "boolean" || typeof notes !== "string" || notes.length > 240)
    fail("W113_POLICY_INVALID");

  const origin = validateOrigin(originText);
  const publishedMs = validateUtc(publishedAt, "W113_PUBLISHED_AT_INVALID");
  const expiresMs = validateUtc(expiresAt, "W113_EXPIRES_AT_INVALID");
  const now = Date.now();
  if (publishedMs > now + 5 * 60_000 || expiresMs <= now ||
      expiresMs <= publishedMs || expiresMs > publishedMs + 30 * 86_400_000)
    fail("W113_MANIFEST_LIFETIME_INVALID");

  if (typeof signingPrivateKeyPem !== "string" || signingPrivateKeyPem.length < 100 ||
      !Buffer.isBuffer(expectedPublicKeyDer) ||
      expectedPublicKeyDer.length < 64 || expectedPublicKeyDer.length > 256)
    fail("W113_SIGNING_TRUST_NOT_CONFIGURED");

  let privateKey;
  try { privateKey = createPrivateKey(signingPrivateKeyPem); }
  catch { fail("W113_SIGNING_KEY_INVALID"); }
  if (privateKey.type !== "private" || privateKey.asymmetricKeyType !== "ec" ||
      privateKey.asymmetricKeyDetails?.namedCurve !== "prime256v1")
    fail("W113_SIGNING_KEY_NOT_P256");

  const publicKeyDer = createPublicKey(privateKey).export({ format: "der", type: "spki" });
  if (publicKeyDer.length !== expectedPublicKeyDer.length ||
      !timingSafeEqual(publicKeyDer, expectedPublicKeyDer))
    fail("W113_SIGNING_KEY_DOES_NOT_MATCH_PINNED_PUBLIC_KEY");

  const [pkg, app, host, renderer] = await Promise.all([
    hashRegularFile(packagePath, "W113_PACKAGE_FILE_INVALID"),
    hashRegularFile(applicationPath, "W113_APPLICATION_FILE_INVALID"),
    hashRegularFile(nativeHostPath, "W113_NATIVE_HOST_FILE_INVALID"),
    hashRegularFile(rendererPath, "W113_RENDERER_FILE_INVALID")
  ]);
  if (pkg.size < MIN_PACKAGE_BYTES || pkg.size > MAX_PACKAGE_BYTES ||
      basename(pkg.path) !== "CELIKOM-Windows-" + version + ".exe" ||
      basename(app.path) !== "CELIKOM.Companion.exe" ||
      basename(host.path) !== "host.cjs" || basename(renderer.path) !== "renderer.js")
    fail("W113_RELEASE_PAYLOAD_LAYOUT_INVALID");

  const packageUrl = new URL(
    "/CELIKOM/Windows/Updates/stable/" + version + "/" + basename(pkg.path), origin
  );
  const manifest = {
    schema: 2, channel: "stable", version, sequence,
    packageUrl: packageUrl.toString(), packageSize: pkg.size, sha256: pkg.sha256,
    publisher: "CELIKOM", publishedAt, expiresAt, minimumVersion: null,
    mandatory, notes, rollback: null,
    applicationSha256: app.sha256,
    nativeHostSha256: host.sha256,
    rendererSha256: renderer.sha256
  };
  const document = Buffer.from(JSON.stringify(manifest, null, 2) + "\n", "utf8");
  if (document.length < 100 || document.length > MAX_MANIFEST_BYTES)
    fail("W113_MANIFEST_SIZE_INVALID");
  const signature = signBytes("sha256", document, { key: privateKey, dsaEncoding: "der" });
  if (signature.length < 64 || signature.length > 80) fail("W113_SIGNATURE_SIZE_INVALID");
  return {
    manifest, document, signature,
    publicKeyDer: Buffer.from(publicKeyDer),
    packageSha256: pkg.sha256
  };
}

async function atomicWrite(filePath, bytes) {
  const destination = resolve(filePath);
  await mkdir(dirname(destination), { recursive: true });
  const temporary = destination + ".tmp-" + process.pid;
  try {
    await writeFile(temporary, bytes, { flag: "wx", mode: 0o644 });
    await rename(temporary, destination);
  } catch (error) {
    await rm(temporary, { force: true }).catch(() => {});
    throw error;
  }
}

function parseArgs(args) {
  const values = new Map();
  const flags = new Set(["--mandatory"]);
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (!key.startsWith("--") || values.has(key)) fail("W113_ARGUMENTS_INVALID");
    if (flags.has(key)) { values.set(key, true); continue; }
    if (i + 1 >= args.length || args[i + 1].startsWith("--")) fail("W113_ARGUMENTS_INVALID");
    values.set(key, args[++i]);
  }
  const required = [
    "--package", "--application", "--native-host", "--renderer", "--version",
    "--sequence", "--origin", "--private-key-file", "--pinned-public-key-der",
    "--output-dir", "--expires-at"
  ];
  for (const key of required) if (!values.has(key)) fail("W113_ARGUMENTS_INVALID");
  return values;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const privateKeyPath = resolve(args.get("--private-key-file"));
  const keyInfo = await lstat(privateKeyPath).catch(() => null);
  if (!keyInfo?.isFile() || keyInfo.isSymbolicLink()) fail("W113_SIGNING_KEY_FILE_INVALID");
  if (process.platform !== "win32" && (keyInfo.mode & 0o077) !== 0)
    fail("W113_SIGNING_KEY_FILE_PERMISSIONS_INVALID");

  const result = await buildStableManifestArtifacts({
    packagePath: args.get("--package"),
    applicationPath: args.get("--application"),
    nativeHostPath: args.get("--native-host"),
    rendererPath: args.get("--renderer"),
    version: args.get("--version"),
    sequence: Number(args.get("--sequence")),
    origin: args.get("--origin"),
    signingPrivateKeyPem: await readFile(privateKeyPath, "utf8"),
    expectedPublicKeyDer: await readFile(args.get("--pinned-public-key-der")),
    expiresAt: args.get("--expires-at"),
    mandatory: args.has("--mandatory"),
    notes: args.get("--notes") ?? ""
  });

  const output = resolve(args.get("--output-dir"));
  await mkdir(output, { recursive: true });
  await atomicWrite(resolve(output, "latest.json"), result.document);
  await atomicWrite(resolve(output, "latest.json.sig"), result.signature);
  await atomicWrite(resolve(output, "manifest-public-key.der"), result.publicKeyDer);
  console.log("W113_SCHEMA2_MANIFEST_GENERATED version=" + result.manifest.version +
    " sequence=" + result.manifest.sequence + " package_sha256=" + result.packageSha256);
}

if (process.argv[1] &&
    import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => {
    console.error(error instanceof Error ? error.message : "W113_MANIFEST_BUILD_FAILED");
    process.exitCode = 1;
  });
}
