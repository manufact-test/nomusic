import { readFile, mkdir, writeFile } from "node:fs/promises";
import { stripTypeScriptTypes } from "node:module";
const root = new URL("../../", import.meta.url);
const sources = ["extension/src/player/core.ts", "extension/src/adapters/yandex-music-adapter.ts"];
const parts = [];
for (const file of sources) parts.push(stripTypeScriptTypes(await readFile(new URL(file, root), "utf8")));
parts.push(`
(() => {
  if (window.top !== window || window.__CELIKOM_ANDROID_SURFACE__) return;
  const adapter = window.__CELIKOM_YANDEX_ADAPTER_V1__.createAdapter(window);
  window.__CELIKOM_ANDROID_SURFACE__ = adapter;
  adapter.mount({onSnapshot() {}, onPlayerEvent() {}});
})();
`);
const output = new URL("app/src/main/assets/", import.meta.url);
await mkdir(output, { recursive: true });
await writeFile(new URL("shared-surface-probe.js", output), parts.join("\n;\n") + "\n");

const playback = [];
for (const file of [...sources, "extension/src/player/original-audio-guard.ts"]) playback.push(stripTypeScriptTypes(await readFile(new URL(file, root), "utf8")));
playback.push(await readFile(new URL("playback-surface.js", import.meta.url), "utf8"));
await writeFile(new URL("mobile-playback.js", output), playback.join("\n;\n") + "\n");
