# CELIKOM Windows W81 — official releases, 2026 history and visible errors (12 November 2026)

**No change to owner's working Windows 0.24.25.** Candidate Windows GUI 0.24.27 in separate branch; native audio module **byte-identical** to 0.24.25, no server, Android or browser extension changes.

## Implementation and release infrastructure

- Exact branch: `experiment/windows-w81-vendor-monitor-compat-visibility-20261112`, forked from W80 CI-verified `3a3ceba6ecc5099d555d691a4fa76621a5b69e73`.
- Exact pre-change backup: `backup/windows-w81-pre-monitor-and-status-exact-20261112`.
- Existing W80 candidate 0.24.26: source and release notes `docs/windows/W80-VENDOR-UPDATE-RECONNECT-20261112.md`.
- Migration/open reminder task: [GitHub issue #48](https://github.com/manufact-test/nomusic/issues/48); stay open until all checks after VPS/Forgejo migration.
- **Backward feed safety:** existing CELIKOM Windows 0.24.26 uses the older `official-yandex-builds-v1.json` parser (it cannot read hexadecimal 2026 build suffixes). **NEVER append 2026 historical hex-version pins to that v1 feed.** W81 uses new `official-yandex-builds-v2.json` with 5 full pins. Both public files live under `support/windows-yandex-compatibility`. Independent `.github/workflows/windows-compatibility-catalog-append-only.yml` prevents accidental deletion/renaming or hash replacement; final CI https://github.com/manufact-test/nomusic/actions/runs/43303122284 **PASS**. Future new Yandex builds need to be added to v2 and also to v1 **only if v1 schema can parse them**, otherwise old clients should receive an appropriate CELIKOM update rather than a broken feed.
- **True hourly schedule must live on default branch**: workflow `.github/workflows/windows-yandex-hourly-release-watch.yml` added to `main` at `2741c403772f6e2837cd27bf748f90dc8d7722c9`, cron `19 * * * *`. This is not a guarantee of exact time: GitHub may delay/drop schedule and disables in inactive public repositories after 60 days.
- Portable Windows script `windows-companion/w81/Watch-YandexWindowsRelease.ps1` can later run under independent cron/Windows runner. It reads the **official Yandex desktop Windows release metadata** `https://music-desktop-application.s3.yandex.net/stable/latest.yml`. This is a real updater feed independently verified with ephemeral Windows CI (HTTP 200, 2026-11-12: version 5.127.0). In some PowerShell versions content returns `byte[]`, so the script explicitly UTF-8 decodes it.
- Script checks exact current version against append-only verified catalog. When unknown, CI downloads **only official Yandex-signed vendor installer** on disposable Windows runner, extracts EXE/ASAR without running vendor installer, validates publisher and exact hashes, and runs image builder + native install/restore sandbox checks. Only a JSON report is published; no original/altered vendor binaries are uploaded.
- New version alerts create an actionable GitHub review issue, deduplicated by version. **Never auto-publish an untested build to consumer catalog**: native sandbox checks cannot prove actual audible replacement or guarantee that Yandex didn't change runtime APIs. A developer first reviews native/audio compatibility, then adds a verified entry to `support/windows-yandex-compatibility`, without removing prior entries.
- If no new version: `already_supported`, no Windows installer download, no alert, minimal cost.
- Migration rule: preserve consumer feed URL or redirect to own domain before disabling old GitHub mirror, and do end-to-end cron/Windows runner/feed update test. GitHub issue #48 tracks this.

## 2026 backward-compatibility inventory

Official signed Windows installers still reachable from original Yandex S3 (HEAD HTTP 200) for:
- February 2026 — `5.86.0.r18727399`
- May 2026 — `5.102.0.r19615975`
- September 2026 — `5.121.2.e45430462d786ebc235511f243ef24745909c790`
- November 2026 — `5.126.1.56270518164a6ebd4b974971490df41224a69d68`
- November 2026 — `5.127.0.r22015925`

All four archives older than 5.127 passed **actual official-signed EXE/ASAR SHA + staged native image builder** on isolated Windows CI: [run 43300824253](https://github.com/manufact-test/nomusic/actions/runs/43300824253). New strict sandbox tests then require actual `NativeIntegrationManager.Install`, native module identity, and byte-for-byte `Restore` of original vendor EXE/ASAR before using the versions; no consumer host files touched. These are *representative 2026 builds*, not a promise that every weekly variant is already approved. Never force people to update official Yandex simply because a later version exists.

The catalog and built-in fallback now retain old 2026 pins **in addition to 5.127**. Legacy `5.126.1` remains backward-compatible with its existing exact supported ASAR; the new signed EXE pin makes it stricter, not broader. Live playback on old historical versions still needs manual owner/candidate QA: a valid native image is not proof of sound. Future versions should be appended, never substituted.

## UI diagnosis exposed to ordinary users

- Pure `UserFacingPlaybackHealth.Host/Track` maps native host errors into visible red/warning states in the **compact popup**, not staff-only diagnostics.
- Red: unsupported/untrusted Yandex, interrupted native installation, module mismatch, `NATIVE_SOURCE_FAILED`, `HOST_ERROR`, stale native heartbeat.
- Yellow: reconnectable reviewed vendor update, `RESOLVING`, `NATIVE_RECOVERING`, fallback to original despite an approved version.
- **No false audible guarantee**: `NATIVE_MAPPING_ACCEPTED` only means the player accepted a replacement source URL, so it's yellow (not “Подмена активна” green). Green header only reflects local connectivity, not verified sound.
- `BridgeServer.LastHeartbeatAt` gives a last-valid-heartbeat timestamp. If the enabled bridge loses heartbeats for over 30s, compact UI surfaces an error.
- Ordinary user can see explanations; support diagnostics remain allowlisted, owner export restrictions preserved.
- W81 GUI tests cover all health cases and identity/entitlement/login safeguards; native audio scripts in `w23` untouched.

## Release/QA gate

- W81 test workflow `windows-w81-monitor-status-checks.yml`: W15 tests, W24 pinned catalog tests, Windows GUI warnings-as-errors.
- W81 archived 2026 official integration lab `windows-w81-watch-candidate-smoke.yml`: signed vendor archives, staging and actual sandbox install+restore.
- W81 candidate installer workflow `windows-w81-2026-status-installer.yml`: builds GUI 0.24.27, exercises old W80 0.24.26 → new W81 0.24.27 with one AppId, preserved decryptable DPAPI login and exact native host+renderer, no touching Yandex files.
- **Do not tell owner to overwrite 0.24.25 tonight**; owner intended music QA on that version tomorrow. W81 installer is only a candidate until all CI are green and physical playback is later verified.
