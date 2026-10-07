# CELIKOM extension

Production Manifest V3 client. Stage 2 contains the versioned player-observation layer: a MAIN-world `YandexMusicAdapter`, an isolated `PlayerBridge` and a diagnostic controller. It determines the exact current Track ID and original master player without changing audio output.

```bash
npm run build
npm test
```

Load `dist/unpacked` through `chrome://extensions`, refresh the Yandex Music tab once, press `Старт` and play a track. The popup reports the detected track and can copy the Stage 2 diagnostics. Account, upload, subscription and production replacement behavior are not part of this stage.

Service-specific DOM, network and route knowledge is isolated in `src/adapters/yandex-music-adapter.ts`. Other extension layers consume only the normalized contracts in `src/player/contracts.ts`. See `../docs/adr/0003-player-state-sources-and-bridge.md` and the Stage 2 live test plan.
