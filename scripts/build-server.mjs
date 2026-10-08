import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { cp, mkdir, readFile, readdir, rm, utimes, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const version = JSON.parse(await readFile(path.join(root, "package.json"), "utf8")).version;
const output = path.join(root, "dist"); const stage = path.join(output, "server-package");
await rm(stage, { recursive: true, force: true }); await mkdir(stage, { recursive: true });
// Allowlist: no .env, user music, vendor, tests or repository metadata.
for (const name of ["bootstrap.php", "composer.json", ".env.example", "README.md", "bin", "config", "cron", "deploy", "migrations", "public", "src"]) {
  await cp(path.join(root, "server", name), path.join(stage, name), { recursive: true });
}
await cp(path.join(root, "docs/deployment/hostinger-private-test.md"), path.join(stage, "HOSTINGER.md"));
async function walk(dir) {
  const files = [];
  for (const entry of (await readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walk(file)); else files.push(file);
  }
  return files;
}
const files = await walk(stage);
for (const file of files) await utimes(file, new Date("1980-01-01T00:00:00Z"), new Date("1980-01-01T00:00:00Z"));
await mkdir(output, { recursive: true });
const name = `celikom-server-${version}.zip`; const archive = path.join(output, name);
await rm(archive, { force: true });
const zip = spawnSync("zip", ["-X", "-9", "-q", archive, ...files.map(file => path.relative(stage, file))], { cwd: stage, stdio: "inherit" });
if (zip.status !== 0) throw new Error("Server package failed");
const hash = createHash("sha256").update(await readFile(archive)).digest("hex");
await writeFile(archive + ".sha256", `${hash}  ${name}\n`);
console.log(`Built private-test deployment package ${archive}`);
