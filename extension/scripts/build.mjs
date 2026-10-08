import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { cp, mkdir, readFile, readdir, rm, stat, utimes, writeFile } from "node:fs/promises";
import { stripTypeScriptTypes } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { contentScriptGroups } from "./content-script-groups.mjs";
import { apiBuildConfig } from "./api-build-config.mjs";

const extensionRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = path.join(extensionRoot, "src");
const outputRoot = path.join(extensionRoot, "dist");
const unpackedRoot = path.join(outputRoot, "unpacked");
const packageJson = JSON.parse(await readFile(path.join(extensionRoot, "package.json"), "utf8"));
const archiveName = `celikom-extension-${packageJson.version}.zip`;
const archivePath = path.join(outputRoot, archiveName);
const epoch = new Date("1980-01-01T00:00:00.000Z");
const unpackedOnly = process.argv.includes("--unpacked-only");

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else files.push(absolute);
  }
  return files;
}

async function compileSources() {
  for (const sourcePath of await walk(sourceRoot)) {
    if (!sourcePath.endsWith(".ts")) continue;
    const relative = path.relative(sourceRoot, sourcePath).replace(/\.ts$/, ".js");
    const outputPath = path.join(unpackedRoot, relative);
    const source = await readFile(sourcePath, "utf8");
    const compiled = stripTypeScriptTypes(source, { mode: "transform", sourceMap: false });
    await mkdir(path.dirname(outputPath), { recursive: true });
    await writeFile(outputPath, compiled, "utf8");
  }
}

async function normalizeTree(directory) {
  for (const file of await walk(directory)) {
    await utimes(file, epoch, epoch);
  }
}

await rm(unpackedRoot, { recursive: true, force: true });
await mkdir(unpackedRoot, { recursive: true });
await compileSources();
for (const group of contentScriptGroups) {
  const parts = await Promise.all(group.modules.map(async (file) => `// ${file}\n${await readFile(path.join(unpackedRoot, file), "utf8")}`));
  await writeFile(path.join(unpackedRoot, group.file), `// CELIKOM ${packageJson.version} ${group.world} dependency bundle\n${parts.join("\n;\n")}\n`, "utf8");
}
const apiConfig = apiBuildConfig(process.env.CELIKOM_API_BASE_URL);
await mkdir(path.join(unpackedRoot, "api"), { recursive: true });
await writeFile(path.join(unpackedRoot, "api", "config.json"), JSON.stringify(apiConfig, null, 2) + "\n");
const sourceManifest = JSON.parse(await readFile(path.join(extensionRoot, "manifest", "manifest.json"), "utf8"));
if (apiConfig.baseUrl && apiConfig.baseUrl !== "https://music.yandex.ru") sourceManifest.host_permissions.push(`${apiConfig.baseUrl}/*`);
await writeFile(path.join(unpackedRoot, "manifest.json"), JSON.stringify(sourceManifest, null, 2) + "\n");
await cp(path.join(extensionRoot, "popup"), path.join(unpackedRoot, "popup"), { recursive: true });
await cp(path.join(extensionRoot, "_locales"), path.join(unpackedRoot, "_locales"), { recursive: true });
await cp(path.join(extensionRoot, "assets"), path.join(unpackedRoot, "assets"), { recursive: true });

const manifest = JSON.parse(await readFile(path.join(unpackedRoot, "manifest.json"), "utf8"));
if (manifest.version !== packageJson.version) {
  throw new Error(`Manifest ${manifest.version} and package ${packageJson.version} versions differ`);
}
for (const group of contentScriptGroups) {
  const entry = manifest.content_scripts.find((script) => script.world === group.world);
  if (JSON.stringify(entry?.js) !== JSON.stringify([group.file])) throw new Error(`Invalid ${group.world} bundle entry`);
}

await normalizeTree(unpackedRoot);
console.log(`Built unpacked extension at ${unpackedRoot}`);

if (!unpackedOnly) {
  await rm(archivePath, { force: true });
  const files = (await walk(unpackedRoot)).map((file) => path.relative(unpackedRoot, file));
  const zipped = spawnSync("zip", ["-X", "-9", "-q", archivePath, ...files], {
    cwd: unpackedRoot,
    stdio: "inherit"
  });
  if (zipped.status !== 0) throw new Error("zip failed while building the extension artifact");

  const bytes = await readFile(archivePath);
  const checksum = createHash("sha256").update(bytes).digest("hex");
  await writeFile(`${archivePath}.sha256`, `${checksum}  ${archiveName}\n`, "utf8");
  const info = await stat(archivePath);
  console.log(`Built ${archivePath} (${info.size} bytes)`);
}
