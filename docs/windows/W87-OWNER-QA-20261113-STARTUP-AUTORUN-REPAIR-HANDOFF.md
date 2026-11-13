# W87 — Owner QA checkpoint, automatic start, module repair UX and no flashing (2026-11-13)

## READ THIS FIRST / immutable recovery point

Owner explicitly requests: **first save all work & this QA evidence, then implement in one controlled batch**, with no changes to currently installed 0.24.30 until new candidate is CI validated. Repo: `manufact-test/nomusic`.
- Exact owner-tested baseline commit `77cd940ea9bb4bb20b70341e33957ee757e45d41`, branch `experiment/windows-w86-02430-source-witness-owner-test-20261113`.
- Backup **`backup/windows-w87-before-autostart-qa-owner-20261113`** = exact W86 starting point.
- Current working **`experiment/windows-w87-autostart-quiet-repair-20261113`**, created at same SHA.
- Owner installed TEST **Windows 0.24.30** from Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.30-TEST-SOURCE-DIAGNOSTICS.exe`. SHA256 `F289167A6106505FCFD46F89BE7B6DA34DAFD2DD27695AF3549F0D1A7BBD1AD8`. Stable rollback `/CELIKOM/Windows/CELIKOM-Windows-0.24.29-PROMO-FIX.exe`, SHA256 `B70B67517A81A0329A197BF65DCFB52660123CDA216CD5881DED8CD20B3173A0`.
- Original user screenshot 0.24.30: right after initial window opened, small **false alarming red** `Модуль CELIKOM устарел. Нажми «Обновить модуль»`; no button by that name. On **«Старт»**, CELIKOM successfully updated native module and opened official Yandex. Initial popup also briefly appears as unstyled boxes/blank before UI controls are rendered.
- User's explicit desired behavior: finished smooth popup on startup; **no misleading red version warning on every boot**. «Старт» should verify/recover native module and subscription, show **only** normal `Идёт загрузка Яндекс.Музыки…` while working, then launch Yandex after successful reconnect; on real failure show *one* short small actionable error. On Windows sign-in, if the owner opted in to autostart, quietly run in tray and **reconnect automatically**, leaving Yandex itself unopened until user opens it. If user last pressed explicit Stop, preserve stopped choice; never auto-enable revoked/expired subscription, unsupported or unsafe vendor build. Never rewrite unknown/untrusted Yandex files.
- Run and verify `0.24.29 → new TEST` in-place with same AppId, DPAPI login preserved, Yandex original hashes unchanged. Tests include manual Stop, no login, revoked entitlement, interrupted installation and offline failures; no false 'connected' UI.
- Prior W81 UI false errors were caused by using event-only heartbeat for liveness (do NOT reintroduce). W86 passive CDP decoder witness remains diagnostic-only; absence of `kUrl` must not be shown as error or change playback. Promo no-blink from W83 MUST remain.

## Owner two real diagnostics: 0.24.30

First snapshot: `Вставленный текст(20261113-080346).txt` (generated 2026-11-13 08:03:06 UTC); active/connected, `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`. Earlier 07:48:13 `NATIVE_UPGRADE_REQUEST` → 07:48:24 `NATIVE_UPGRADE_OK` → `START_ENABLED`. Some resolved original songs (expected where no alternate) and some mapped approved sources. `PlayerAudibleEventObserved=false` and no exact `NativeMediaUrlExactMatchObserved`; do not claim proven sound. The device user heard normal playback.

Latest snapshot: `Вставленный текст(20261113-084941).txt` generated **08:49:25 UTC**. `AppVersion=0.24.30.0`, `NativeModuleVersion=0.24.25` (the native *internal* version marker is intentionally unchanged), **`NativeModuleMatchesApp=true`**, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, signed in. User reports real music listening **seems stable**.
- Many `RESOLVE_APPROVED`, `SOURCE_BATCH_MAPPED`, `NATIVE_MAPPING_ACCEPTED`, `PLAYER_NET_HTTP_PARTIAL`, finished downloads. No `DecoderErrorObserved`. `PlayerAudibleEventObserved=false`, `NativeMediaUrlExactMatchObserved=false`, `NativeMediaUrlSignedFieldsIntactObserved=true`: no independent proof of audible alternative. Continue issue #52.
- **Important incident at 08:49:22 UTC**: `PLAYER_URL_EXPIRED_AT_REQUEST|resource_id=23` → `PLAYER_NET_HTTP_FORBIDDEN` → `PLAYER_403_PHP_INVALID_AUDIO_TOKEN`. About 0.3 seconds later the source was re-resolved, fresh signed URL was requested (`PLAYER_URL_SIGNED_FIELDS_INTACT`), and `PLAYER_NET_HTTP_PARTIAL` returned again. This is **real transient expired-token 403 followed by recovery**, not a persistent failure and not proof that music was interrupted. Investigate refresh-at-resume/token TTL guard; do NOT unilaterally change 2026 playback paths until tests demonstrate issue. User said music plays fine.
- There is `PLAYER_NET_FAILED` while switching/pausing a stream; appears transient, no `DecoderErrorObserved`. Preserve existing recovery.
- 15-min ring-buffer exported; does not necessarily include original launch event. Two snapshots are the evidence; originals supplied in current conversation, no need to ask the owner again.

## Work plan / safety gates

1. Save this report and prepend essential summary to `docs/windows/NEXT-CHAT.md` **before any code edits**.
2. Fix exact **startup repaint** where WinForms handle is shown prior to compact layout; consider `Opacity=0` until layout and first render then show, without blocking actual tray launch.
3. Replace false "Обновить модуль" warning (nonexistent button) with actual Start recovery state; background autostart should reconcile quietly.
4. Implement opt-in **Windows login autostart to tray** with user control and explicit saved last-start/stop preference; safe opt-out, single-instance handling, no forced opening of Yandex on Windows boot.
5. On autostart, **server revalidate account, entitlement + exact native module hash / official Yandex signature** before enabling; if only local module hash outdated, safely Upgrade() or proper recovery with existing backup, and do not claim success prematurely. Unknown Yandex builds fail closed without rewriting.
6. Cover tests and CI; keep backups. User will QA a later clearly named candidate. Do not modify/overwrite current Library 0.24.29 or 0.24.30.

## Open issues

- [#44](https://github.com/manufact-test/nomusic/issues/44) owner playback QA not fully closed.
- [#52](https://github.com/manufact-test/nomusic/issues/52) real audible/native decoder witness still not proven.
- [#48](https://github.com/manufact-test/nomusic/issues/48) preserve hourly vendor update monitor after private-server migration; pending migration.
