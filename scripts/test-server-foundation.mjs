import { spawnSync } from "node:child_process";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const serverRoot = path.join(root, "server");

async function walk(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && entry.name === "vendor") continue;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else files.push(absolute);
  }
  return files;
}

const composer = JSON.parse(await readFile(path.join(serverRoot, "composer.json"), "utf8"));
if (composer.require?.php !== ">=8.3") throw new Error("composer.json does not enforce PHP 8.3");

const phpFiles = (await walk(serverRoot)).filter((file) => file.endsWith(".php"));
for (const file of phpFiles) {
  const source = await readFile(file, "utf8");
  if (!source.includes("declare(strict_types=1);")) {
    throw new Error(`${path.relative(root, file)} must enable strict_types`);
  }
}

const phpVersion = spawnSync("php", ["--version"], { encoding: "utf8" });
if (phpVersion.error?.code === "ENOENT") {
  console.log(`Server structure validated (${phpFiles.length} PHP files); runtime test deferred to PHP 8.3 CI.`);
  process.exit(0);
}
if (phpVersion.status !== 0) throw new Error(phpVersion.stderr || "Unable to inspect PHP runtime");

for (const file of phpFiles) {
  const lint = spawnSync("php", ["-l", file], { encoding: "utf8" });
  if (lint.status !== 0) throw new Error(lint.stderr || lint.stdout);
}

const smoke = spawnSync("php", [path.join(serverRoot, "tests", "database.php")], { stdio: "inherit" });
if (smoke.status !== 0) process.exit(smoke.status || 1);
if (process.env.DB_NAME) {
  const uploads = spawnSync("php", [path.join(serverRoot, "tests", "uploads.php")], { stdio: "inherit" });
  if (uploads.status !== 0) process.exit(uploads.status || 1);
  const admin = spawnSync("php", [path.join(serverRoot, "tests", "admin.php")], { stdio: "inherit" });
  if (admin.status !== 0) process.exit(admin.status || 1);
  const auth = spawnSync("php", [path.join(serverRoot, "tests", "auth.php")], { stdio: "inherit" });
  if (auth.status !== 0) process.exit(auth.status || 1);
  const http = spawnSync(process.execPath, [path.join(serverRoot, "tests", "http.mjs")], { stdio: "inherit" });
  if (http.status !== 0) process.exit(http.status || 1);
}
console.log(`Server runtime validation passed with ${phpVersion.stdout.split("\n")[0]}.`);
