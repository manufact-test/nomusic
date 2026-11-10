# W56 — Yandex telemetry breaks CELIKOM signed audio URL; native source-only guard (2026-11-10)

## Status
**A specific implementation defect is now demonstrated against the pinned original Yandex 5.126.1 source flow, and a narrow W56 workaround passes local/synthetic HTTP and session tests. Owner audible playback is NOT YET CONFIRMED.** Installed owner version stays **0.24.6** until owner explicitly updates. Internal candidate **0.24.7**, not a public/production release. Android and backend unchanged.

Owner W51 evidence: 7 genuine native Media GETs to CELIKOM resource IDs 139/89, 7 HTTP403, no 200/206, no CORS errors; other Yandex tracks audible. The 0.24.6 diagnostics did not record actual native query or error body, so **the exact seven request URLs cannot be retrospectively proven**.

## Root mechanism, read-only original Yandex analysis
- The *original, vendor-signed* ASAR was cryptographically verified by fixed SHA; W55 static audit https://github.com/manufact-test/nomusic/actions/runs/42795212512 SUCCESS; explicit pinned flow assertions https://github.com/manufact-test/nomusic/actions/runs/42796327933 SUCCESS.
- Original `DownloadInfoSource` builds `src` by concatenating `data.urls[0] + getQueryParamsString() + "#t=" + positionSec`. The latter method may return `?vsid=<opaque>&source_index=<number>`. It does **not** merge with an existing query.
- Original Yandex `TelemetryPlugin.beforeMediaHandler` writes `mediaSourceData.vsid` and `mediaSourceData.sourceIndex` if they exist and were undefined. The original `DownloadInfoSource` exposes both fields, so even RAW MP3 can receive the extra query when that hook is active. Earlier W52's conclusion that MP3 normally cannot receive it was incomplete: it looked only at construction, **not the later telemetry hook**.
- CELIKOM `ResolveService` signs `/api/v1/audio/{replacement_id}?token=HMAC&expires=E&sid=S`. When native media concatenates its query naively, the URL becomes `...&sid=S?vsid=X&source_index=N#t=...`. PHP parses `sid` as `S?vsid=X`: strict SID syntax fails and `AudioController` returns `403 invalid_audio_token`. Without SID, the `expires` field is likewise spoiled and rejects. A valid local signed-link fetch (e.g. old W48 probe's 206) can differ from the later real native Media GET for this reason.
- This path provides a concrete source-based explanation consistent with W51's 403s. **Not yet confirmed on the owner's exact 7 GETs**, which were redacted. Do not claim audible fix until owner hears replacement and genuine GET returns 200/206.

## Narrow W56 fix — Windows native source only
`windows-companion/w22/native-resource-adapter.mjs`, applied AFTER the original strict `validateCelikomGrant` and ONLY to an approved, validated CELIKOM native playback source:
- Append inert trailing field `&celikom_native_query_guard=0` to the MEDIA `downloadInfo.urls[0]` and matching `downloadInfo.url`. The original signed grant and its HMAC/expiry/session/token checks remain unchanged. Never modify native Yandex's original stream URLs.
- If Yandex then adds `?vsid=X&source_index=N#t=T`, PHP sees `sid=S` unchanged and ignored `celikom_native_query_guard=0?vsid=X`, plus unrelated `source_index=N`; MP3 fragment `#t=T` still works.
- Do **not** append `#` before the Yandex metadata (would swallow `#t` and impair seek); do not strip `sid`, weaken HMAC, change server access policy, disable telemetry globally, patch Yandex vendor implementation or add a new media engine.
- W53 native URL comparison will honestly emit `PLAYER_URL_SIGNED_FIELDS_INTACT` rather than exact byte match when the harmless guard is present. This is expected, not a signature failure.

## Verified safeguards
- Node native tests: single source, batch, Next, Stop, unapproved/foreign grant fail-closed, actual simulated Yandex getter concatenation preserving token/expires/sid and seek fragment, and no guard on original songs.
- PHP smoke: unguarded appended `?vsid` is rejected 403; guarded URL streams Range **206**; forged HMAC and expired token still **403**.
- PHP/MySQL Stage10 entitlement (disposable test DB, no production): valid guarded session-bound SID streams **206**, broken SID **403**, revoked session **403**. Stage-only full workflow https://github.com/manufact-test/nomusic/actions/runs/42796387968 **SUCCESS** (all jobs).
- Genuine signed original Yandex disposable install/host/restore with code guard and original vendor hash verified: https://github.com/manufact-test/nomusic/actions/runs/42796125980 **SUCCESS**, without Yandex account or owner authentication.
- Earlier W53 safety: W41 https://github.com/manufact-test/nomusic/actions/runs/42792654175 **SUCCESS**, W23 https://github.com/manufact-test/nomusic/actions/runs/42791811325 **SUCCESS**, W20 staging https://github.com/manufact-test/nomusic/actions/runs/42796126093 **SUCCESS**.
- Owner's installed program and production API have NOT been changed during this W56 work.

## Version 0.24.7 candidate and deployment gate
- Update stage metadata in `w15/Celikom.Companion.csproj`, `w20/installer/CELIKOM.iss`, `w23/host.cjs`, `w23/package.json`, W15 updater tests, and W20 internal staging workflow; Inno **AppId, InstallDir, native backup/restore policy, DPAPI credential location and update mechanism remain unchanged**.
- Candidate file: `CELIKOM-W56-SIGNED-QUERY-GUARD-UNSIGNED.exe`; unsigned internal testing only. Full 0.24.7 W20 packaging CI https://github.com/manufact-test/nomusic/actions/runs/42796898660 (final result to verify).
- Before owner trial: verify 0.24.6 → 0.24.7 in-place upgrade on fresh disposable Windows: same AppId, exactly one uninstaller, DPAPI/session bytes preserved, native host and renderer version 0.24.7, no original Yandex changes; retain rollback.
- On passing CI, deliver **actual** EXE through verified ChatGPT Library `CELIKOM/Windows` as a direct file card. NEVER invent sandbox links. Owner should test one approved track and normal track, pause and seek, then upload 15-minute W53 diagnostics if any issue. **Do not call audible playback PASS until real owner test.**

## Rollbacks
- Frozen before W56: `backup/windows-w55-before-native-signed-query-guard-20261110` at `b56ad543f15c1e0970f38a6b4429ff59c6f2eb9a`.
- Previously accepted owner 0.24.6: `backup/windows-w50-owner-0246-audio-403-pre-w51-docs-20261110` at `38b9e0d691b47a11a800eb4c6d26d07fc47068fe`.
- W53 export safety regression fixed and preserved; release guard still denies public release without owner audio acceptance.
