# W62 — CELIKOM Windows 0.24.10 compact extension UI / real services (2026-11-10)

## Owner's authoritative new diagnostics

Original user file: `1.zip` → `1.txt` (`GeneratedUTC=2026-11-10T12:15:40.9299591Z`), provided by owner after real test of **Windows 0.24.9**.

Owner confirms real audible replacement works, native **pause/seek and Start/Stop work, significantly less abrupt, no clicking ("пшики")**. Small delay is tolerable. Do NOT "fix audio" by riskily changing Yandex player volume, switching queue, or replacing approved W60 `reloadEntity("QUALITY_CHANGE")` path.

Safe diagnostic analysis:
- `AppVersion=0.24.9.0`, `NativeModuleVersion=0.24.9`, `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `SignedIn=true`.
- `STOP_DISABLED` at 12:15:24.388 → `NATIVE_TOGGLE_RELOAD_REQUEST` 12:15:24.758 (**370 ms**) → `NATIVE_TOGGLE_RELOAD_OK` 12:15:25.511 (**753 ms** inside vendor source reload) → `PLAYER_ENGINE_STARTED` 12:15:25.590.
- `START_ENABLED` at 12:15:27.432 → `NATIVE_TOGGLE_RELOAD_REQUEST` 12:15:27.788 (**356 ms**) → `RESOLVE_APPROVED` 12:15:27.844 → `NATIVE_TOGGLE_RELOAD_OK` 12:15:28.524 (**736 ms**) → `PLAYER_CDP_EVENT_START` 12:15:28.858.
- During Start a few `PLAYER_NET_FAILED` events coexisted with valid signed URL preservation, HTTP 206 and finishing resource. No recorded 403, CORS or decoder errors; however `PlayerAudibleEventObserved=false` and mappings/network alone **do not prove audible replacement**. Owner's direct audio report is separate evidence.
- Most of the delay happens in official Yandex source reload. **No further audio speed-up attempted** in W62. Retain accepted W61 native polling 260ms, source logic, controls.

## Backups and branch

- Owner accepted baseline 0.24.9 at `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` pointing to `44e69d78b459ed512862819280ebdb8b3dbc7e7d`. Never mutate.
- Previous backups 0.24.8 (owner-tested toggle) `backup/windows-w60-0248-owner-toggle-pass-before-ux-20261110` and accepted 0.24.7 remain.
- Work only on `experiment/windows-stop-lifecycle-20261110`. **Do not change Android Test.50, production, original Yandex vendor files or owner sessions**.

## W62 implementation

The user compared two screenshots and correctly rejected the wide 0.24.9 Window as not resembling the extension. W62 refactors **native WinForms UI** to match actual `extension/popup/popup.html` + `popup.css` width and order: header, side-by-side Start/Stop, Return Original, Upload, Suggest, server access, current song, red account prompt, support, authorized-only diagnostic link. No large Home/Account nav, no exposed API, dev buttons, or unneeded footer instructions.

- Native `MainWindow.cs` now uses `BuildCompactPopup()` in `CompactPopup.cs` and `CompactPopupActions.cs`; built-in account/password fields and existing one-app update are preserved.
- Account: working sign in, registration/email verification, password recovery, sign out. Promo code activation, entitlements and Moscow-formatted lifetime/trial/subscription state **actually fetched from production CELIKOM API**, never mocked display.
- Support: `/api/v1/support` genuine authenticated normal tickets and typed current-song reports with true numeric Yandex current track + categories, idempotency key; song title/artist not invented.
- Contributions: real `/api/v1/tracks/version-status`, `/api/v1/track-requests` and guarded `/api/v1/uploads` multipart upload, authenticated account and explicit rights confirmation, MP3/M4A 30 MiB maximum, actual server duration validation. Current song Track ID is transferred read-only from the already observed official Yandex player via `current-source-refresh.mjs`, renderer, host heartbeat, existing `BridgeServer.LastSong`. Existing audio adapter switching and `reloadEntity` were not modified.
- Windows desktop form width about 308px, mimics extension 292px body; compact accordion account & support; no global technical controls. `PopupButton` now respects left alignment. The first actual WinForms screenshot exposed overlap of Start and Stop; fixed native DockStyle and added automated screenshot-geometry test. New preview screenshot and geometry CI **SUCCESS**.
- **Known parity limits**: Windows Return Original currently stops global CELIKOM (same as Stop), rather than extension's per-track bypass; user may notice. Windows upload requires explicit duration seconds because it cannot yet trust vendor duration metadata, unlike extension's automatic duration inspection. Current song shows exact numeric ID rather than artist/title if vendor metadata unavailable. Do not present as 100% feature parity or attempt unverified audio hooks for these.
- Existing Windows private staff Ctrl+Shift+U update picker remains; normal user cannot see diagnostic export, staff is checked by live authenticated allowlist in `CelikomApi`.
- Version `0.24.10`, **same Inno AppId** and install path as 0.24.9; never second application or logout.

## Verified CI, executable & Library

- Full W62 owner-candidate Windows compile, backend interaction contracts, renderer/source and native regression, disposable in-place installer smoke: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42817316962 (build source SHA `eb1c9f2e1de69091c14f0e275d99f000f94d4d00`).
- Actual WinForms screenshot rendering + geometry guard: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42817228046
- Passive native current-Track-ID and W60 player source regression tests: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42816041611
- Independent **real owner installed 0.24.9 → W62 0.24.10 same-user DPAPI, one app/uninstaller, native module version and Yandex untouched**: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42817785847
- GitHub Actions artifact ID **13764517942**, ZIP SHA256 `44186ff4bec4293f0a6b325cc4a3c91c89a1f12ee4e01e06cfab2a7bddcbaca8`.
- Windows unsigned EXE **`CELIKOM-W62-EXTENSION-PARITY-UNSIGNED.exe`**, exact SHA256 `ed2dff94d3d59bc600432f7f9b826ecc13850778937944a07bc198dbee6a5cde`, 43,536,342 bytes. Source built from W62 code before docs-only commits.
- Stored in ChatGPT Library `/CELIKOM/Windows/CELIKOM-W62-EXTENSION-PARITY-UNSIGNED.exe` (file `file_000000006a7481f4bd310f424f863a46`, library ID `libfile_74fc8b4adb388191bdd261bd7eca4f99`). Re-materialized and compared SHA256 with signed run log: **exact match**.

## Next owner action / acceptance gate

Run current 0.24.9 update picker (staff shortcut Ctrl+Shift+U) and select W62 EXE. The update goes over 0.24.9, without uninstall/relogin. On a Windows machine test compact UI, actual account lifelong promo, account/login, support submit (ONLY when intentionally wishing to send a ticket), track ID detection, upload/suggestion visibility, Start/Stop, pause, seek, Next, MyWave. No real server-side test promo, support ticket or audio was sent during CI.

If sound has regressed, restore accepted 0.24.9 backup/build immediately. **0.24.10 real-machine audio and support UI still await owner testing.** No public release until owner accepts.
