# CELIKOM extension

Production Manifest V3 client. Stage 2 contains the versioned player-observation layer: a MAIN-world `YandexMusicAdapter`, an isolated `PlayerBridge` and a diagnostic controller. It determines the exact current Track ID and original master player without changing audio output.

```bash
npm run build
npm test
```

Load `dist/unpacked` through `chrome://extensions`, press `Старт` and play a track. Version `0.2.1` also injects the packaged observer into a previously open Yandex Music tab. When updating an already-running old build, refresh the music tab once so its page-world observer and detached media are initialized with the new version. The popup reports the detected track and can copy the Stage 2 diagnostics. Account, upload, subscription and production replacement behavior are not part of this stage.

Bootstrap uses `chrome.scripting` with the existing Yandex host permission. If Chrome denies site access, the popup reports `connection.error` and `connection.detail` instead of waiting forever. Give the extension access to `music.yandex.ru` in Chrome's extension settings, then press `Повторить`. There is no alternate access path or remote script loading.

Service-specific DOM, network and route knowledge is isolated in `src/adapters/yandex-music-adapter.ts`. Other extension layers consume only the normalized contracts in `src/player/contracts.ts`. See `../docs/adr/0003-player-state-sources-and-bridge.md` and the Stage 2 live test plan.
