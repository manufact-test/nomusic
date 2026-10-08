import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { contentScriptGroups } from "./content-script-groups.mjs";

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
assert(manifest.permissions?.includes("scripting"), "Packaged-script recovery requires scripting permission");
assert(!manifest.permissions?.includes("tabs"), "Broad tabs permission is not allowed in the foundation");
assert(manifest.host_permissions?.length === 1, "Exactly one development host permission is expected");
assert(manifest.host_permissions[0] === "https://music.yandex.ru/*", "Unexpected host permission");

const mainWorld = manifest.content_scripts.find((entry) => entry.world === "MAIN");
const isolatedWorld = manifest.content_scripts.find((entry) => entry.world === "ISOLATED");
assert(manifest.content_scripts.length === 2, "Exactly MAIN and ISOLATED content-script groups are required");
assert(mainWorld?.run_at === "document_start", "MAIN-world adapter must start at document_start");
assert(isolatedWorld?.run_at === "document_start", "ISOLATED controller must start at document_start");
for (const group of contentScriptGroups) {
  const entry = manifest.content_scripts.find((script) => script.world === group.world);
  assert(JSON.stringify(entry.js) === JSON.stringify([group.file]), `${group.world} must inject one complete dependency bundle`);
  const bundle = await readFile(path.join(unpackedRoot, group.file), "utf8");
  let offset = -1;
  for (const file of group.modules) {
    const marker = `// ${file}\n`;
    const next = bundle.indexOf(marker);
    assert(next > offset, `Missing/out-of-order ${file} in ${group.file}`);
    assert(bundle.includes(await readFile(path.join(unpackedRoot, file), "utf8")), `Bundle differs from ${file}`);
    offset = next;
  }
}
assert(manifest.web_accessible_resources?.length === 1, "Only the demo audio resource may be exposed");
assert(JSON.stringify(manifest.web_accessible_resources[0]) === JSON.stringify({ resources: ["assets/test-audio.mp3"], matches: ["https://music.yandex.ru/*"] }), "Unexpected public resource boundary");

const referenced = [
  manifest.background.service_worker,
  manifest.action.default_popup,
  ...manifest.content_scripts.flatMap((entry) => entry.js ?? []),
  ...manifest.web_accessible_resources.flatMap((entry) => entry.resources ?? [])
];

for (const relative of referenced) {
  const info = await stat(path.join(unpackedRoot, relative)).catch(() => null);
  assert(info?.isFile(), `Manifest references missing file: ${relative}`);
}

console.log(`Validated production extension manifest ${manifest.version}.`);
