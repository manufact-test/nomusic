import { readFile, writeFile, mkdir, cp, rm, readdir } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { contentScriptGroups } from "../../extension/scripts/content-script-groups.mjs";

const source = path.resolve("extension/dist/unpacked");
const target = path.resolve(process.argv[2] || "/tmp/CELIKOM-Native-Experiment-001");
if (target === source || target.startsWith(path.resolve("extension") + "/")) throw Error("isolated_output_required");
await rm(target, { recursive: true, force: true }); await mkdir(target, { recursive: true });
await cp(source, target, { recursive: true });
const manifest = JSON.parse(await readFile(path.join(target, "manifest.json"), "utf8"));
if (manifest.version !== "0.4.73") throw Error("accepted_0473_build_required");
manifest.version = "0.4.74"; manifest.name = "CELIKOM · Native experiment 001";
manifest.version_name = "0.4.74-native-experiment-001";
await writeFile(path.join(target, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
const corePath = path.join(target, "player/core.js");
await writeFile(corePath, (await readFile(corePath, "utf8")).replace('"0.4.73"', '"0.4.74"'));
const script = file => readFile(new URL(file, import.meta.url), "utf8");
for (const group of contentScriptGroups) {
  const parts = [];
  for (const file of group.modules) {
    if (file === "player/replacement-controller.js") {
      const parser = (await readFile(path.join(source, "upload/mp3-duration.js"), "utf8")).replaceAll("export function ", "function ");
      parts.push(`(function(){${parser}\nglobalThis.__CELIKOM_NATIVE_MP3_DURATION__=mp3DurationMs;})();`);
      for (const name of ["prefetch-coordinator.js", "desktop-prefetch-adapter.js", "native-controller.js"]) parts.push(await script(name));
    } else parts.push(await readFile(path.join(target, file), "utf8"));
  }
  if (group.world === "MAIN") {
    for (const name of ["engine-port.js", "native-source.js", "native-session.js", "native-runtime.js"]) parts.push(await script(name));
  }
  await writeFile(path.join(target, group.file), parts.join("\n;\n"));
}
const files = [];
async function walk(folder) {
  for (const entry of (await readdir(folder, { withFileTypes: true })).sort((a,b) => a.name.localeCompare(b.name))) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) await walk(file); else files.push(path.relative(target, file));
  }
}
await walk(target);
const archive = target + ".zip"; await rm(archive, { force: true });
const result = spawnSync("zip", ["-X", "-q", archive, ...files], { cwd: target });
if (result.status !== 0) throw Error("archive_failed");
const bytes = await readFile(archive);
const receipt = { version: manifest.version_name, base: "0.4.73", sourceCommit: process.env.GITHUB_SHA || null,
  bytes: bytes.length, sha256: createHash("sha256").update(bytes).digest("hex"),
  limitations: ["experimental native source only", "MP3 with zero gain only", "complete-file download before switching", "real signed-in playback not yet verified"] };
await writeFile(archive + ".json", JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify({ archive, ...receipt }));
