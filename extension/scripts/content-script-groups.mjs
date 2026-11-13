// One deterministic classic script per execution world. Chrome and recovery
// injection both execute exactly this dependency order as a single script.
export const contentScriptGroups = Object.freeze([
  { world: "MAIN", file: "player/main-world-bundle.js", modules: [
    "player/core.js",
    "adapters/yandex-music-adapter.js",
    "player/original-audio-guard.js",
    "player/main-world-entry.js"
  ] },
  { world: "ISOLATED", file: "content/controller-bundle.js", modules: [
    "player/core.js",
    "player/player-bridge.js",
    "player/sync-engine.js",
    "player/replacement-player.js",
    "player/fail-open-controller.js",
    "player/replacement-controller.js",
    "content/controller.js"
  ] }
]);
