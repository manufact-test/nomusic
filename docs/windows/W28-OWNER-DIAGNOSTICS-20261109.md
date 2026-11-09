# W28 — Owner-first diagnostics for Windows CELIKOM 0.24.1 (2026-11-09)

## Status
- W27 real audio blocker **FAIL remains**. NO audible approved replacement confirmed.
- A new dedicated backup precedes changes: `backup/windows-w28-before-diagnostics-20261109` at W27 `099d71c5030cba3d8fb72efd051e4bf82bc2ad7b`.
- Development branch: `experiment/windows-companion-integration-20261108`.
- **One installer** in Windows W20 CI, named `CELIKOM-W28-DIAGNOSTIC-UNSIGNED`, version 0.24.1. Internal only; not a release.
- No original Yandex, shared API/backend, Android, browser extension or production modified in these commits.

## What changed
1. Main UI has a **«Скачать диагностику»** button beside «Открыть Яндекс.Музыку». Click, choose a TXT location, send file to developer. No terminal, env vars, folder browsing or manual logs.
2. Dedicated bounded, rolling logs in `%LOCALAPPDATA%/CELIKOM/Windows/`: `companion-events.log(.1)` for .NET and `native-events.log(.1)` for Electron. Ring buffer 256. Export reads only strictly allowlisted lines: UTC, code, optional numeric trackId. Rotates at 384 KiB each.
3. .NET includes Start/Stop, native bridge state, resolve (approved/miss/network failure), pairing heartbeat statuses, native install/recovery and error categories (not exception text).
4. Main process observes resolve relay, success/failure, renderer delivery, bridge availability and state. Renderer reports exact file-info requests/return shapes, source mapping/fallback, stalled native metadata, resolver timeout, and observable HTMLAudio playback/pause/seek/error transitions. Resource Timing observes only CELIKOM audio URL path without exporting URL or query; HTTP status is only reported when exposed by browser.
5. Export explicitly distinguishes **source mapping was returned** vs **audio was audibly decoded**. Absence of media events means `NOT_OBSERVED`, not success.
6. All export lines are validated on read. No emails, passwords, access/refresh/bridge tokens, cookies, signed URL/query or file paths. Numeric Yandex track IDs only when observed.
7. CI contract tests cover source-only mapping and redacted diagnostic export.

## Owner test (only AFTER CI green)
- Update/install CELIKOM 0.24.1 from completed W28 internal artifact; install over 0.24.0 without manually editing Yandex.
- Start CELIKOM, launch ordinary Yandex, play known problematic track e.g. Гуф «Новогодняя», record observed pause behavior. Compare with disabled playback.
- Click **«Скачать диагностику»** on the main tab, save TXT and send it. If Windows blocks save, choose a writable user folder.
- Do not enter Yandex credentials into CELIKOM. Do not disable Defender. Do not modify Yandex manually.
- Check diagnostics show SOURCE_MAPPED / SOURCE_SYNTHETIC_RESPONSE / MEDIA_REQUEST_SEEN / MEDIA_PLAY / MEDIA_PAUSE and/or NOT_OBSERVED. This localizes whether breakage lies before/after native file-info.
- Status stays **FAIL** until sound + native pause/seek/Next confirmed by owner.

## Known technical limits and next task
- A CELIKOM Start during already-playing Yandex track does not force file-info refresh. Need real logs to distinguish cache from failure.
- If no HTMLAudio element exists, MEDIA_* will not appear; WebAudio decoder may not be observable via current hooks. Resource Timing can show only URLs loaded via renderer, and status can be hidden cross-origin.
- Existing W26 can synthesize a replacement file-info envelope when native metadata stalls. Such an envelope is **suspect**, not proven the reason for immediate pause. Do not change player behavior speculatively before owner log.
- Meaning of **PNR** was not found in current Windows source/handoff and was not invented. Owner term needs definition before any module is claimed present.
- Once owner TXT is available: identify first failed stage; apply minimal correction to actual Yandex file-info/decoder, preserve fallback/restore, verify in disposable CI and real owner playback.
