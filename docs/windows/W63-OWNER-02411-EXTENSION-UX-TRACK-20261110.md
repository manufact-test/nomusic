# CELIKOM Windows W63 / 0.24.11 — owner UI parity trial (2026-11-10)

## Owner's actual feedback driving W63

User installed and tested 0.24.10. The accepted native audio baseline **still plays, pauses, seeks, switches tracks and Start/Stop works**. Owner **rejected the UI**: unnecessary Return Original button; Start mislabeled Repeat; long Yandex launch with no progress; asymmetric gutters; blank signed-in Account pane; Support form hidden below visible area; raw Track ID instead of title; uploads and suggestions did not show green existing/pending result or preflight; native dropdowns/inputs did not resemble extension. User wants the **actual** extension `extension/popup/popup.html`, `popup.css`, `popup.ts`, `version-status.ts`, `auth-popup.ts`, `support.ts` as source of truth.

## Backups

- Best previous user-audio-accepted 0.24.9: `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` at `44e69d78b459ed512862819280ebdb8b3dbc7e7d`. Do not mutate.
- Owner-rejected GUI 0.24.10, preserved to roll back audio: `backup/windows-w62-02410-owner-ui-rejected-before-w63-20261110` at `25101ccfb4fbb09e255e3b10a1664e8c69de4b6e`.
- Exact built W63 0.24.11 source: `backup/windows-w63-02411-built-ci-await-owner-20261110` at `266beacfcfa524eeb9ecae91d44b9316ec257286`. **The W63 source is frozen pending owner trial.**

## What is actually implemented in W63 (experiment branch)

- `CompactPopup.cs`: removed Return Original; `Старт` always the label; normal signed-out red Account CTA; **fixed actual W62 root cause**: layout hid every account child and never set Visible=true again; now real account forms and promo expand. Compact 308px width, shorter height, symmetric 16px gutters; supports auto-scroll to newly expanded section, status and detailed support form stay reachable. Native title `CELIKOM`, footer version larger. Account login, registration, recovery and promo remain backed by real CELIKOM endpoints.
- `PopupSelect.cs`: dark extension-palette dropdowns (no white OS selection surface); `PopupFilePicker.cs`: dashed dark chooser with arrow icon and selected file state. Native upload displays explicit rights checkbox, progress, Cancel confirmation, and file metadata; duration is auto-populated if the currently observed player provides `durationMs`, with a manual seconds fallback otherwise.
- `CompactPopupActions.cs`: current-song `/api/v1/tracks/version-status` read **before showing a form**. `approved` and `pending` both show green result cards, no upload/suggest form; `none` opens actual upload/suggest. Re-check on submit and server still rejects race-condition duplicates. A song switch invalidates stale UI/pending responses and never assigns prior song's success to next song. Uploads send the real current track and bounded artist/title + stable idempotency request key, rights declaration and multipart file; `ProgressReadStream.cs` reports local transmitted-file read percentages. Do not pretend this is server-side processing progress or extension's IndexedDB background upload.
- Real current track name/artist and duration: `w60/current-source-refresh.mjs` observes only current official Yandex player entity (not preload), reads *bounded* `meta.title` / `artists` / `durationMs` if available. `w23/renderer-entry.mjs` and `host.cjs` pass display metadata via existing authenticated localhost heartbeat to `BridgeServer.cs`. No raw metadata added to diagnostic logs. If Yandex does not supply metadata fields, UI **falls back to numeric Track ID** and/or optional manual duration: actual user-machine behavior **not yet proven**.
- `MainWindow.cs`: Start asks whether to open Yandex when not running, launches verified desktop EXE (protocol fallback); displays connecting/loading text until native heartbeat, with honest longer-launch guidance after ~22 seconds. No fabricated loading percentages. Installer still handles module upgrade through Start, with existing safety prompt; NO independent update/restore developer buttons in public UI.
- Diagnostics stays restricted to the **same two allowlisted admin email SHA-256 identities as the Chrome extension** with authenticated /auth/me recheck on each export. Button `Скопировать диагностику` now actually writes to clipboard, no surprise file picker. Admin `Ctrl+Shift+D` saves a TXT, `Ctrl+Shift+U` opens signed-in staff updater picker.
- Native music source reload / signed URL guard / Yandex pause/seek/MyWave logic **not touched**. New current-entity observer is read-only except for the previously accepted reload. No production API, original Yandex vendor file, Android Test.50 or production release was modified. **Actual W63 audio behavior still requires owner test**.

## Tests and provenance

- W63 packaged Windows owner-candidate installer full native contract tests, self-contained binary and disposable Win32 install/uninstall: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42824296777. Exact code build SHA `266beacfcfa524eeb9ecae91d44b9316ec257286`.
- Actual Windows WinForms screenshot suite with explicit assertions for visible Start/Stop, **account/email/password/login**, Support Send, song issue category, upload file picker and green existing-version card: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42824296883. Never pass a blank child.
- W60 native paused/current-song read-only regression: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42822622446.
- Independent **0.24.10 → 0.24.11 one-app same-user DPAPI session bytes, one Inno uninstaller, module identity, original vendor untouched**: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42824740871.
- Artifact ZIP id `13768535851` name `CELIKOM-W63-EXTENSION-UX-TRACK-UNSIGNED`, ZIP SHA256 `b274c9fbf6769525fc2850b3ab3ea9bb8f78c82e72313cccd32d080a2b78322c`.
- EXACT unsigned EXE `CELIKOM-W63-EXTENSION-UX-TRACK-UNSIGNED.exe`, 43,543,132 bytes, SHA256 `591e76abfab8573770fb34c88cc809f85d175f1c1649b61abd8e3b95e0f5a276`. Downloaded from GitHub, SHA matched Windows CI, uploaded ChatGPT Library `/CELIKOM/Windows/CELIKOM-W63-EXTENSION-UX-TRACK-UNSIGNED.exe` file `file_00000000850c81f4a77794566d9616c7` and **materialized from Library and SHA revalidated**.
- New source documentation after build only: no code changed since W63 installer SHA.

## Owner acceptance test (next action)

Run W63 EXE over installed 0.24.10 without uninstall/re-login. Explicitly check:
1. Full compact layout + equal gutters, no Return Original, Start label never Repeat, Yandex launch prompt and clear waiting message.
2. Account opens and **content actually appears** (email/benefits/promo/logout as relevant). Support opens and Send is scroll-reachable. Only two admin identities see diagnostics, ordinary user not.
3. Existing song shows **green status** on upload AND suggestion, WITHOUT submit. Missing song shows actual form. Check live track title/artist/duration; do NOT assume present until personally observed. Do not send actual file or support ticket unless intentionally testing a real submission.
4. **Audio regression:** Start/Stop on playing song, pause, seek, Next and MyWave stay as accepted 0.24.9/0.24.10. No click/pop or lengthy stalls. Revert to 0.24.10 if regression; never mutate accepted 0.24.9 baseline.

This is a PRIVATE owner-candidate, NOT publicly released or owner-accepted. No further source modification until owner test.
