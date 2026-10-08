import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const required = [
  ".github/workflows/ci.yml",
  ".github/workflows/extension-build.yml",
  "android/README.md",
  "docs/adr/0001-monorepo-and-runtime-baseline.md",
  "docs/adr/0002-public-development-private-release.md",
  "docs/adr/0003-player-state-sources-and-bridge.md",
  "docs/adr/0004-local-playback-and-guard-leases.md",
  "docs/analytics/event-catalog.md",
  "docs/analytics/metric-definitions.md",
  "docs/product/client-ui-principles.md",
  "docs/test-plans/CELIKOM-STAGE2-PLAYER-INTEGRATION.md",
  "docs/test-plans/CELIKOM-STAGE3-PLAYBACK.md",
  "docs/project-status.md",
  "extension/manifest/manifest.json",
  "extension/tsconfig.json",
  "server/composer.json",
  "server/public/index.php"
];

for (const relative of required) {
  const info = await stat(path.join(root, relative)).catch(() => null);
  if (!info?.isFile()) throw new Error(`Required foundation file is missing: ${relative}`);
}

const rootPackage = JSON.parse(await readFile(path.join(root, "package.json"), "utf8"));
if (!rootPackage.workspaces?.includes("extension")) throw new Error("extension workspace is not registered");
if (rootPackage.private !== true) throw new Error("monorepository package must remain private");

const composer = JSON.parse(await readFile(path.join(root, "server", "composer.json"), "utf8"));
if (composer.require?.php !== ">=8.3") throw new Error("Server must require PHP >=8.3");
if (composer.autoload?.["psr-4"]?.["Celikom\\"] !== "src/") throw new Error("Server PSR-4 mapping is invalid");

const ui = await readFile(path.join(root, "docs", "product", "client-ui-principles.md"), "utf8");
for (const control of ["Старт", "Стоп", "Вернуть оригинал", "Добавить трек"]) {
  if (!ui.includes(control)) throw new Error(`Client UI contract is missing ${control}`);
}

const privacy = await readFile(path.join(root, "docs", "adr", "0002-public-development-private-release.md"), "utf8");
if (!privacy.includes("No public client release") || !privacy.includes("Stage 18")) {
  throw new Error("Private-release gate is not explicit");
}

console.log("Repository foundation contract validated.");
