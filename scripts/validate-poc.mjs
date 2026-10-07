import { readFile, stat, readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extensionRoot = path.join(projectRoot, "spikes", "player-poc");
const manifestPath = path.join(extensionRoot, "manifest.json");
const packagePath = path.join(projectRoot, "package.json");

function fail(message) {
  throw new Error(message);
}

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else files.push(absolute);
  }
  return files;
}

const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const packageJson = JSON.parse(await readFile(packagePath, "utf8"));
if (manifest.manifest_version !== 3) fail("manifest_version must be 3");
if (!manifest.minimum_chrome_version) fail("minimum_chrome_version is required");
if (manifest.version !== packageJson.version) fail("Manifest and package versions must match");
if (!manifest.permissions?.includes("scripting")) fail("scripting permission is required for self-recovery");
if (!Array.isArray(manifest.content_scripts) || manifest.content_scripts.length !== 2) fail("Expected MAIN and ISOLATED content scripts");
if (!manifest.content_scripts.some((entry) => entry.world === "MAIN")) fail("MAIN-world bridge is missing");
if (!manifest.content_scripts.some((entry) => entry.world === "ISOLATED")) fail("ISOLATED controller is missing");

const declaredFiles = new Set([
  manifest.background?.service_worker,
  "background/upgrade-cleanup.js",
  manifest.action?.default_popup,
  ...Object.values(manifest.icons || {}),
  ...manifest.content_scripts.flatMap((entry) => entry.js || []),
  ...manifest.web_accessible_resources.flatMap((entry) => entry.resources || [])
].filter(Boolean));

for (const relative of declaredFiles) {
  const info = await stat(path.join(extensionRoot, relative)).catch(() => null);
  if (!info?.isFile()) fail(`Missing manifest file: ${relative}`);
}

for (const locale of ["ru", "en"]) {
  JSON.parse(await readFile(path.join(extensionRoot, "_locales", locale, "messages.json"), "utf8"));
}

const files = await walk(extensionRoot);
for (const file of files.filter((item) => item.endsWith(".js"))) {
  const check = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
  if (check.status !== 0) fail(`Syntax error in ${path.relative(projectRoot, file)}\n${check.stderr}`);
  const source = await readFile(file, "utf8");
  if (/\beval\s*\(|\bnew\s+Function\s*\(/.test(source)) fail(`Remote-code-like construct found in ${file}`);
}

const audio = await stat(path.join(extensionRoot, "assets", "test-audio.mp3"));
if (audio.size < 1024) fail("Test audio asset is unexpectedly small");
if (audio.size > 40 * 1024 * 1024) fail("Test audio asset exceeds the MVP ceiling");

console.log(`Validated CELIKOM PoC ${manifest.version}: ${files.length} files, ${(audio.size / 1024 / 1024).toFixed(2)} MiB test asset.`);
