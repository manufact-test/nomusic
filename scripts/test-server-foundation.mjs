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

// Every schema introduced by migrations must be exportable by the restore path.
// This guards future additions as well as Stage11/12 journals.
const snapshotSource = await readFile(path.join(root, ".github/scripts/hostinger-stage5-remote.php"), "utf8");
const lists = [...snapshotSource.matchAll(/\$(?:tables|optional)\s*=\s*\[([\s\S]*?)\];/g)];
const snapshotTables = new Set(lists.flatMap((match) => [...match[1].matchAll(/'([a-z_]+)'/g)].map((name) => name[1])));
for (const name of await readdir(path.join(serverRoot, "migrations"))) {
  if (!name.endsWith(".sql")) continue;
  const migration = await readFile(path.join(serverRoot, "migrations", name), "utf8");
  for (const match of migration.matchAll(/CREATE TABLE(?: IF NOT EXISTS)?\s+([a-z_]+)/g)) {
    if (!snapshotTables.has(match[1])) throw new Error(`Backup omits migration table ${match[1]}`);
  }
}

const phpFiles = (await walk(serverRoot)).filter((file) => file.endsWith(".php"));
for (const file of phpFiles) {
  const source = await readFile(file, "utf8");
  if (!source.includes("declare(strict_types=1);")) {
    throw new Error(`${path.relative(root, file)} must enable strict_types`);
  }
}

const promoForm = spawnSync(process.execPath, ["--test", path.join(serverRoot, "tests", "promo-form.test.mjs")], { stdio: "inherit" });
if (promoForm.status !== 0) process.exit(promoForm.status || 1);

const disclosure = spawnSync(process.execPath, ["--test", path.join(serverRoot, "tests", "reward-disclosure.test.mjs")], { stdio: "inherit" });
if (disclosure.status !== 0) process.exit(disclosure.status || 1);

const scrollBrowser = spawnSync(process.execPath, [path.join(serverRoot, "tests", "reward-disclosure-browser.mjs")], { stdio: "inherit" });
if (scrollBrowser.status !== 0) process.exit(scrollBrowser.status || 1);

const incidentBrowser = spawnSync(process.execPath, [path.join(root, "scripts", "test-incident-browser.mjs")], { stdio: "inherit" });
if (incidentBrowser.status !== 0) process.exit(incidentBrowser.status || 1);

const popupScroll = spawnSync(process.execPath, [path.join(root, "scripts", "test-popup-scroll-browser.mjs")], { stdio: "inherit" });
if (popupScroll.status !== 0) process.exit(popupScroll.status || 1);

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
  const support = spawnSync("php", [path.join(serverRoot, "tests", "support.php")], { stdio: "inherit" });
  if (support.status !== 0) process.exit(support.status || 1);
  const promos = spawnSync("php", [path.join(serverRoot, "tests", "promos.php")], { stdio: "inherit" });
  if (promos.status !== 0) process.exit(promos.status || 1);
  const incidents = spawnSync("php", [path.join(serverRoot, "tests", "incidents.php")], { stdio: "inherit" });
  if (incidents.status !== 0) process.exit(incidents.status || 1);
  const uploads = spawnSync("php", [path.join(serverRoot, "tests", "uploads.php")], { stdio: "inherit" });
  if (uploads.status !== 0) process.exit(uploads.status || 1);
  const admin = spawnSync("php", [path.join(serverRoot, "tests", "admin.php")], { stdio: "inherit" });
  if (admin.status !== 0) process.exit(admin.status || 1);
  const auth = spawnSync("php", [path.join(serverRoot, "tests", "auth.php")], { stdio: "inherit" });
  if (auth.status !== 0) process.exit(auth.status || 1);
  const entitlement = spawnSync("php", [path.join(serverRoot, "tests", "entitlement.php")], { stdio: "inherit" });
  if (entitlement.status !== 0) process.exit(entitlement.status || 1);
  const billing = spawnSync("php", [path.join(serverRoot, "tests", "billing.php")], { stdio: "inherit" });
  if (billing.status !== 0) process.exit(billing.status || 1);
  const referrals = spawnSync("php", [path.join(serverRoot, "tests", "referrals.php")], { stdio: "inherit" });
  if (referrals.status !== 0) process.exit(referrals.status || 1);
  const rewards = spawnSync("php", [path.join(serverRoot, "tests", "rewards.php")], { stdio: "inherit" });
  if (rewards.status !== 0) process.exit(rewards.status || 1);
  const rewardPolicy = spawnSync("php", [path.join(serverRoot, "tests", "reward-policy.php")], { stdio: "inherit" });
  if (rewardPolicy.status !== 0) process.exit(rewardPolicy.status || 1);
  const automaticRewards = spawnSync("php", [path.join(serverRoot, "tests", "automatic-rewards.php")], { stdio: "inherit" });
  if (automaticRewards.status !== 0) process.exit(automaticRewards.status || 1);
  const http = spawnSync(process.execPath, [path.join(serverRoot, "tests", "http.mjs")], { stdio: "inherit" });
  if (http.status !== 0) process.exit(http.status || 1);
}
console.log(`Server runtime validation passed with ${phpVersion.stdout.split("\n")[0]}.`);
