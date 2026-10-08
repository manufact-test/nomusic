# CELIKOM extension

Manifest V3 client. Stage 2 observation was accepted on `0.2.1`. Stage 3 (`0.3.2`) adds `ReplacementController`, `ReplacementPlayer`, `SyncEngine`, `OriginalAudioGuard` and `FailOpenController`, using an opt-in packaged synthetic fixture for one exact Track ID. Real files and backend resolution are not connected yet.

0.3.1 fixes the reported 0.3.0 `normalizeTrackId` startup crash. Dependencies resolve at controller construction; manifest and recovery injection use the same single deterministic bundle per world. Polling does not reinject a failed controller. Refresh the music tab after updating so the old immutable page globals are discarded.

0.3.2 excludes short data-audio utility elements from master selection and preserves an existing exact guard during metadata-only seek/buffering while pausing replacement. New guards still require playable data. Catalog duration independently validates the native clock; changing a guarded stream restores original and holds the stale Track ID until an exact different ID or explicit Start. Diagnostics add `playback.activationCount`, `restoreCount` and `lastRestore` with safe binding reasons. The owner's 0.3.1 run confirmed startup and active replacement, but same-track restore loops keep the stability gate open.

```bash
npm run build
npm test
```

Load `dist/unpacked` through `chrome://extensions` and refresh the Yandex Music tab once after updating. Press `Старт` and play a track. Open the collapsed developer section and press `Тестировать текущий трек` to bind the synthetic demo. Leave the test ID empty for original-only playback. `Вернуть оригинал` bypasses the current ID until an exact different track or an explicit Start; `Стоп` persists globally in local storage. Developer details are collapsed by default; `Добавить трек` only opens a coming-soon message and uploads nothing.

Bootstrap uses `chrome.scripting` with the existing Yandex host permission. If Chrome denies site access, the popup reports `connection.error` and `connection.detail` instead of waiting forever. Give the extension access to `music.yandex.ru` in Chrome's extension settings, then press `Повторить`. There is no alternate access path or remote script loading.

Service-specific DOM, network and route knowledge stays in `src/adapters/yandex-music-adapter.ts`. Guard commands require an exact current track/media binding and a session-generation lease. MAIN independently stops CELIKOM media and restores the latest logical volume/mute on heartbeat loss (12 s visible / 120 s hidden), pagehide or session replacement. A new generation cannot be released by a stale lease.

Tests execute compiled scripts in VM/mock browser environments; this is not proof of real Chromium media behavior. Complete `../docs/test-plans/CELIKOM-STAGE3-PLAYBACK.md` before accepting Stage 3. The next stages connect the API/MySQL contract, then Hostinger and authorized real MP3 fixtures.
