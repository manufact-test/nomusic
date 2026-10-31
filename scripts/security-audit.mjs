import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

// This repository currently has no third-party runtime npm/composer packages.
// Fail when that changes so a vulnerability-aware dependency audit is added
// before introducing a new dependency. This is not an OS/Actions CVE audit.
const lock = JSON.parse(await readFile("package-lock.json", "utf8"));
assert.equal(lock.lockfileVersion, 3);
for (const [name, pkg] of Object.entries(lock.packages)) {
  assert.ok(["", "extension", "node_modules/@celikom/extension"].includes(name),
    "New dependency requires an explicit vulnerability audit");
  if (name.startsWith("node_modules/")) assert.equal(pkg.link, true);
}
const composer = JSON.parse(await readFile("server/composer.json", "utf8"));
assert.ok(Object.keys(composer.require).every(name => name === "php" || name.startsWith("ext-")),
  "New Composer dependency requires a locked vulnerability audit");

const root = "extension/dist/unpacked";
const manifest = JSON.parse(await readFile(path.join(root, "manifest.json"), "utf8"));
assert.equal(manifest.manifest_version, 3);
assert.ok(!manifest.externally_connectable);
assert.ok(!manifest.content_security_policy.extension_pages.includes("unsafe-eval"));
assert.ok(manifest.permissions.every(value => ["storage", "scripting", "offscreen"].includes(value)));
assert.ok(manifest.host_permissions.every(value => value === "https://music.yandex.ru/*"
  || value === "https://darkred-camel-588676.hostingersite.com/*"));
const forbidden = [/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
  /\bghp_[A-Za-z0-9]{30,}\b/, /\bgithub_pat_[A-Za-z0-9_]{40,}\b/,
  /\bAKIA[0-9A-Z]{16}\b/, /\bsk-[A-Za-z0-9]{32,}\b/];
let files = 0;
async function inspect(dir) {
  for (const entry of await readdir(dir, {withFileTypes: true})) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) { await inspect(file); continue; }
    assert.ok(!/\.(?:map|pem|p12|pfx|jks|keystore)$/.test(entry.name), "Forbidden build material");
    assert.notEqual(entry.name, ".env");
    if (/\.(?:js|json|html|css)$/.test(entry.name)) {
      const source = await readFile(file, "utf8");
      assert.ok(!forbidden.some(pattern => pattern.test(source)), "Credential pattern in client build");
      assert.ok(!source.includes("sourceMappingURL="), "Client source map reference");
    }
    files++;
  }
}
await inspect(root);
console.log(`Security build gate PASS: ${files} client files, bounded permissions, no source maps/private key patterns; no external package dependencies.`);
