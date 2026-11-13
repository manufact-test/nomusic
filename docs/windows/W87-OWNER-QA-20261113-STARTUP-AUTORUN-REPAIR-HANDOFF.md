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

## W87 implementation complete — 0.24.31 TEST, Windows CI GREEN

- **GitHub run success**: https://github.com/manufact-test/nomusic/actions/runs/43398111483, artifact `14024195652` https://github.com/manufact-test/nomusic/actions/runs/43398111483/artifacts/14024195652.
- Exact installer SHA256 `762B9F4166B611BB78FDD7CE4F1F8311E2DA05E7171CC3E3EC3EC6017061EF83`; size **43,545,042 bytes**; verified after ZIP extraction. CELIKOM EXE unsigned as before.
- Windows in-place 0.24.30→0.24.31 CI: **`W87_02430_TO_02431_INPLACE_DPAPI_AND_NATIVE_UNCHANGED_PASS`**. Same AppId; session.dpapi remains decryptable and byte-identical. Both native audio assets host.cjs and renderer.js identical to W86 / 0.24.30. Native sound pipeline unchanged.
- **Persistent Library upload success**: `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.31-AUTORUN-TEST.exe` Library ID `libfile_9bb79f49b7908191a11150cafcd9c5fb`. User's 0.24.30 and stable 0.24.29 files untouched.
- `WindowsLaunchSettings.cs`: opt-in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\CELIKOM` with quoted `--background` command; remember last explicit Start/Stop and account-specific hashed identity in HKCU, **never** store server grant or plaintext email in Run preference. Autostart default OFF until owner enables it once via tray right-click → **Запускать с Windows**. Toggling off removes own Run entry.
- `Program.cs`: single instance via Windows named mutex, second manual launch signals existing tray to show instead of creating second bridge. Original `--restore-native` still works.
- `MainWindow.cs`: transparent until layout complete first paint; `--background` never shows popup or taskbar at sign-in. Manual Start performs existing entitlement/native checks, refreshes an already approved module without redundant "обновить" dialog, and automatically opens installed official Yandex when needed. First-time native installation retains owner consent.
- `MainWindow.Autostart.cs`: repeatable silent reconnect only with prior user Start intent, same account, fresh **non-activating** `GetEntitlementAsync` and exact native hash match; if signed Yandex vendor update or already-authorized old native module, stage safe repair only if Yandex is **not running**, re-read native state + revalidate entitlement after repair. If user is listening, defer; never silently close Yandex at Windows login; no forced Yandex launch. Network errors or unknown/tampered versions fail closed; 2-min retry and Stop/account-switch epoch guards. Legitimate manual Stop disables reboot resume.
- `UserFacingPlaybackHealth.cs` and `CompactPopup.cs`: normal after-app-update module mismatch is a small neutral grey hint **«Нажми „Старт“, чтобы обновить модуль CELIKOM.»**, never misleading red or nonexistent "Обновить модуль" button. Dangerous untrusted builds remain true errors.
- `MainWindow.RefreshHostCoreAsync`: if a running module hash no longer matches installed assets, disable bridge rather than falsely green connected.
- Tests added for quoted startup command, opt-in/opt-out, account/installation isolation, remembered Stop, no false red after app upgrade. Existing native audio integration / W15 entitlement suites pass.

### Owner field QA NOT yet confirmed

After installing **0.24.31 TEST** over **0.24.30**, listen normally (same sound), check first window has no unstyled square flash, manually press Start after module upgrade (one native refresh and Yandex opens), then right-click CELIKOM tray → enable **Запускать с Windows**, verify Windows reboot/sign-in shows CELIKOM **only in tray**, opening Yandex manually yields working alternatives. Explicit Stop, reboot: must stay off; network outage, trial expiry, unsupported Yandex: must never enable. If necessary roll back to 0.24.30 TEST (saved Library) or 0.24.29 stable. CI is not a substitute for real reboot/playback QA.

The latest owner's expired-audio-token 403 was **already followed by signed URL HTTP 206**; no alteration to source/streaming logic in W87. Do not claim proof of audible decoder source; issue #52 stays open.
