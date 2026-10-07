import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const extensionRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const unpackedRoot = path.join(extensionRoot, "dist", "unpacked");
const manifest = JSON.parse(await readFile(path.join(unpackedRoot, "manifest.json"), "utf8"));
const packageJson = JSON.parse(await readFile(path.join(extensionRoot, "package.json"), "utf8"));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(manifest.manifest_version === 3, "Manifest V3 is required");
assert(manifest.version === packageJson.version, "Manifest/package version mismatch");
assert(manifest.minimum_chrome_version, "minimum_chrome_version is required");
assert(manifest.background?.type === "module", "Background worker must be an ES module");
assert(manifest.permissions?.includes("storage"), "storage permission is required");
assert(!manifest.permissions?.includes("tabs"), "Broad tabs permission is not allowed in the foundation");
assert(manifest.host_permissions?.length === 1, "Exactly one development host permission is expected");
assert(manifest.host_permissions[0] === "https://music.yandex.ru/*", "Unexpected host permission");

const referenced = [
  manifest.background.service_worker,
  manifest.action.default_popup,
  ...manifest.content_scripts.flatMap((entry) => entry.js ?? [])
];

for (const relative of referenced) {
  const info = await stat(path.join(unpackedRoot, relative)).catch(() => null);
  assert(info?.isFile(), `Manifest references missing file: ${relative}`);
}

console.log(`Validated production extension manifest ${manifest.version}.`);
