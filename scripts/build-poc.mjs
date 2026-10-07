import { cp, mkdir, readFile, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extensionRoot = path.join(projectRoot, "spikes", "player-poc");
const distRoot = path.join(projectRoot, "dist");
const manifest = JSON.parse(await readFile(path.join(extensionRoot, "manifest.json"), "utf8"));
const releaseName = `CELIKOM-POC-001-v${manifest.version}`;
const staging = path.join(distRoot, releaseName);
const archive = path.join(distRoot, `${releaseName}.zip`);
const sourceArchive = path.join(distRoot, `${releaseName}-source.zip`);

const unitTests = spawnSync(process.execPath, ["--test", path.join(extensionRoot, "tests", "core.test.cjs")], { stdio: "inherit" });
if (unitTests.status !== 0) process.exit(unitTests.status || 1);

const fixtureSmoke = spawnSync(process.execPath, [path.join(projectRoot, "scripts", "smoke-fixture.mjs")], { stdio: "inherit" });
if (fixtureSmoke.status !== 0) process.exit(fixtureSmoke.status || 1);

const validation = spawnSync(process.execPath, [path.join(projectRoot, "scripts", "validate-poc.mjs")], { stdio: "inherit" });
if (validation.status !== 0) process.exit(validation.status || 1);

await mkdir(distRoot, { recursive: true });
await rm(staging, { recursive: true, force: true });
await rm(archive, { force: true });
await rm(sourceArchive, { force: true });
await cp(extensionRoot, staging, { recursive: true });
await rm(path.join(staging, "tests"), { recursive: true, force: true });
await rm(path.join(staging, "assets", "icons", "icon-source.svg"), { force: true });

const zipped = spawnSync("zip", ["-q", "-r", archive, "."], { cwd: staging, stdio: "inherit" });
if (zipped.status !== 0) process.exit(zipped.status || 1);

const sourceZipped = spawnSync("zip", [
  "-q", "-r", sourceArchive,
  "README.md", "CHANGELOG.md", "package.json", "docs", "scripts", "spikes"
], { cwd: projectRoot, stdio: "inherit" });
if (sourceZipped.status !== 0) process.exit(sourceZipped.status || 1);

console.log(archive);
console.log(sourceArchive);
