# CELIKOM extension

Production-oriented Manifest V3 foundation. Stage 1 establishes packaging, message contracts and fail-open control surfaces only. The accepted playback implementation remains in `../spikes/player-poc` until its contracts are migrated under the Stage 2–3 test gates.

```bash
npm run build
npm test
```

Load `dist/unpacked` through `chrome://extensions` for foundation smoke testing. The popup intentionally exposes only local start/stop/original controls; account, upload, subscription and production replacement behavior are not part of this stage.
