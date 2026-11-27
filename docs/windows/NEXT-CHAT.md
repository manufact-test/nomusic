# ACTIVE CELIKOM WINDOWS — W188 audio recovery / Yandex 5.129.0 (27 November 2026)

**Read this active handoff first:** \`docs/windows/W188-W174-51290-RESTORE-HANDOFF-20261127.md\`.

Then read:
1. \`docs/windows/W188-02461-AUDIO-BASELINE-AND-YANDEX-51290-INVESTIGATION-20261127.md\` — original owner diagnostic and W174 baseline.
2. \`docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md\` — historical source/owner-accepted W174 context only; its old mainline task is not the current task.

## Current exact state

- Repository: \`manufact-test/nomusic\`.
- Branch: \`recovery/windows-w174-02454-known-good-20261126\`.
- HEAD: \`d0de9824c5e03422a9d6f928f17715de07bb76ba\`.
- Official Yandex 5.129.0 compatibility workflow [45965695251](https://github.com/manufact-test/nomusic/actions/runs/45965695251): **SUCCESS**; 32/32 Node tests, W24 20, W21 41, W15 477, GUI build 0 warnings/0 errors, official 5.129.0 signature/hash/native-image/byte-exact-restore and ASAR audits passed.
- Exact Yandex version: \`5.129.0.r22295238\`; ASAR SHA256: \`4c6623a9f7780e245ddda2e94afad7392166a05479a237e6112589d3f09275e1\`.
- Validation artifact ID: \`15182926152\` (report + ASAR + audit JSON; **not an installer**).
- Separate isolated FlokiNET/private handoff run [45965695138](https://github.com/manufact-test/nomusic/actions/runs/45965695138), job \`140394244238\`: **in progress at handoff**. Check it before doing anything else. No owner installer has been confirmed or delivered.
- W174 audio baseline files remain unchanged; exact hashes and W188 changes are in the active handoff doc.

## Immediate task for the next chat

Continue from the current branch and existing Actions runs. First check run \`45965695138\`; do not rerun green compatibility run \`45965695251\` or create a duplicate build. Determine whether the FlokiNET job produces a valid owner package or only stages an existing signed transfer. If a package is required, finish it through the approved path, verify the exact artifact and only then hand it to the owner.

**Do not claim the problem is fixed yet:** the CI proves 5.129.0 compatibility and the W188 provider bridge contracts, not audible replacement on the owner's PC. Do not merge to main, add stable catalog pin, publish OTA, or touch Android/server/extension.

The historical W173/W170/W169 and earlier handoffs below are retained for context. Their old immediate tasks are superseded by this W188 handoff; do not execute them as current instructions.

---

# CURRENT WINDOWS W173 — make the latest working build canonical on main (21 November 2026)

Read these documents first:

1. `docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md` — exact next task: make the latest working Windows version canonical on main and safely remove obsolete Windows-only clutter.
2. `docs/windows/W173-START-UX-AND-OWNER-UPLOAD-AUDIT-20261121.md` — latest Windows code, Yandex 5.128.0, Start UX correction, package and owner upload audit.
3. `docs/windows/W170-WINDOWS-UPLOAD-AUTO-CLEANUP-20261121.md` — original upload contract and Windows-side preflight details.

## Immediate next-chat task

The owner wants the latest working CELIKOM Windows version to become the one canonical version in GitHub `main`. Main should no longer misleadingly show an older Windows version while the latest implementation lives on a side branch. After the correct version is established on main, clean up obsolete Windows-only experimental branches/PR clutter so the repository is easier to navigate.

**Target:** W173 / CELIKOM Windows app **0.24.54.0**, Update Supervisor **0.24.54.0**, Native host/module **0.24.31**, compatible with official Yandex Music **5.128.0**.

The owner explicitly confirmed that he installed the exact W173 0.24.54.0 package, checked it, and it works. Treat the W173 source/package checkpoint as the owner-accepted production candidate. Do not ask for another confirmation, repeat broad runtime tests, or rebuild without a concrete failure.

## Exact repository state

- Repository: `manufact-test/nomusic`.
- Default branch: `main`.
- `main` HEAD at handoff: `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- Main Windows app and Update Supervisor still declare **0.24.48**. This is older than the current owner candidate.
- Current Windows work branch: `experiment/windows-w172-yandex-51280-compat-20261121`.
- W173 source/package checkpoint: `0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`; later commits on the W173 branch are documentation/handoff updates. Resolve the live branch HEAD from GitHub before making any ref changes.
- W173 app and Update Supervisor: **0.24.54.0**; embedded native host/module marker: **0.24.31**.
- Live W173 comparison: 96 commits ahead, 0 behind, 29 changed files. The W173 code/package checkpoint is 0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d; the 14 commits after that checkpoint are documentation-only handoff updates. The reviewed inventory contains Windows W15/W20/W24/W81 code, Windows CI/workflows and Windows docs, with no Android, server or browser-extension source.
- Main pre-W170 backup exists: `backup/windows-main-pre-upload-cleanup-20261121` at `affb7b225d2e7eb2835f53294e975a1e60bb758b`. Still create a fresh pre-consolidation backup before the mainline operation.

## W173 implementation and verification

- W172 added the exact signed official Yandex 5.128.0 EXE/ASAR pair to the compatibility catalog and preserves prior approved integration state.
- W173 fixes the owner-visible Start flow: keep the normal “Подождите, идёт подключение к Яндекс Музыке” message; do not show the extra red vendor-update prompt; do not invalidate an in-flight Start when the exact verified Yandex update is discovered. Unknown/modified files remain fail-closed.
- W173 does not change playback, gain, VPN, audio routing, native host version, Android, extension, account/access, or server behavior.
- W172 candidate CI: [44894403337](https://github.com/manufact-test/nomusic/actions/runs/44894403337) — SUCCESS.
- W20 safe internal installer stage: [44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351) — SUCCESS.
- W15: **469 passed**; W21: **41 passed**; W24: **20 passed**; GUI warnings-as-errors build passed; disposable install, in-place upgrade, uninstall and package integrity checks passed.
- Internal owner package: EXE `CELIKOM-W173-START-UX-02454-UNSIGNED.exe`; ZIP `CELIKOM-Windows-0.24.54.zip`; artifact ID `14703029534` on run `44894407351`; expires **1 December 2026, 10:30 UTC**. Package is unsigned/internal only. EXE SHA256: `da5877bb01dca6048ce85cb07881f663c3a16cb81ec1f3b16074837bf9b60f33`; ZIP SHA256: `d719af9688d74230440887707b9a6cd1c8e2b08af6026cd406c909fd4d3fb4b3`.

## Upload cleanup — verified; do not add logging

- Shared server cleanup version 0.4.78 is already deployed. Do not redeploy it as part of Windows consolidation.
- Windows W170 preserves the original selected MP3 bytes and sends them to the existing authenticated `POST /api/v1/uploads`; server normalizes, measures, fully decodes and stores the canonical file.
- Private read-only audit [44895271863](https://github.com/manufact-test/nomusic/actions/runs/44895271863): **13/13** post-activation uploads passed stored hash, size, duration, canonical-normalizer and full-decode checks; 9 approved, 4 pending, 0 failed checks.
- The audit reads canonical stored files after cleanup, so it cannot identify retrospectively which raw upload had tags removed. Do not misstate this as “no source metadata found”.
- **Owner decision: do not add a per-song cleanup journal, removed-tag counters, extra telemetry, or raw-file retention.** The required outcome is clean, working songs accepted and damaged files rejected. The existing pipeline and audit cover that. Do not create a logging project or complicate the uploader.

## PRs and branches — handle carefully

- PR **#65** is still an open draft, but its head is the older W170 branch `experiment/windows-w170-mainline-20261121` at `6ce4cc21352912ab31578190007042397e083f64`. It is not the W173 branch. Do not merge it as-is.
- PR **#64** is a closed duplicate of the old W170 work.
- PR **#62** is the separate already-deployed server upload-cleanup review; do not fold it into Windows mainline consolidation.
- PR **#66** is separate admin rejected/disabled cleanup; do not fold it into Windows mainline consolidation.
- Preserve all `backup/*` branches, Android A1 branches, and server/extension branches. These are not obsolete Windows experiments.
- Candidate obsolete Windows-only work branches can be reviewed after main is validated: old W170 branch and superseded W172/W173 working branches. Delete only after the latest code is safely on main, a fresh backup exists, CI is green, and the owner-facing build is identified. Never bulk-delete by name pattern.

## Required execution sequence

1. Inspect current main, W173 branch HEAD, full commit graph, full file diff, PR #65 and all related workflow status. Confirm no unreviewed server/Android/extension changes are being brought across.
2. Use the exact W173 0.24.54.0 package/source already installed and accepted by the owner. It is an internal unsigned owner build, not a public signed release; do not ask the owner to repeat acceptance.
3. Create a fresh immutable backup branch from current main before changing main.
4. Open a new PR from W173 to main (PR #65 points at the older W170 branch; do not silently pretend it contains W173). Ensure the PR description records W173, 0.24.54.0, Yandex 5.128.0 and the verification evidence.
5. Run full main CI, Windows integration CI, W20 safe installer validation and any required repository gates on the exact merge candidate. Fix only actual failures.
6. Merge the reviewed W173 PR to main after the exact PR-head checks pass. Verify main's app, supervisor and installer versions all read 0.24.54.0 and the embedded native host/module marker remains 0.24.31; verify Yandex 5.128.0 compatibility and the W173 Start UX fix.
7. Close PR #65 as superseded by the W173 mainline PR. Leave PR #62 and #66 untouched.
8. Only then remove clearly obsolete, unprotected Windows experiment branches/duplicate PR clutter. Preserve backups and all Android/server/extension work. Verify branch and PR lists after cleanup.
9. Update this handoff with the final main SHA, merged PR, CI run IDs, retained backup branch and exactly which obsolete Windows refs were removed.

## Hard rules

- One canonical Windows production line: `main`.
- Do not reset or force-push main.
- Do not delete `backup/*` branches.
- Do not touch Android, browser extension, server deployment, auth/access, billing, playback, volume, VPN, routing or unrelated admin moderation work.
- Do not merge PR #62 or #66 as part of this task.
- Do not add per-song cleanup logs or retain source MP3s.
- No new installer unless a code change is necessary. The existing W173 package is an internal unsigned owner-review build, not a signed public release.
- Work in one complete block, with no unnecessary intermediate reports. Stop only for an owner decision or a real blocker.

---

# PREVIOUS WINDOWS W170 — owner upload runtime testing (21 November 2026)


This section is historical context for the original W170 upload change. The active handoff is the W173 section at the top of this file.

## Repository state

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/windows-w170-mainline-20261121`
- PR: [#65 — W170 Windows upload compatibility](https://github.com/manufact-test/nomusic/pull/65) — still open as a draft on the older W170 branch; it is superseded by the W173 candidate and must not be merged as-is.
- Product: CELIKOM Windows only.
- Owner-accepted source baseline: app **0.24.51.0**, native **0.24.32**.
- W170 internal build: app **0.24.52.0**, update supervisor **0.24.52.0**, native host/module unchanged.
- Main pre-work backup: `backup/windows-main-pre-upload-cleanup-20261121` @ `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- At the W173 handoff, `main` still contains Windows 0.24.48. The owner has requested W173 0.24.54.0 become canonical on main; follow the W173 mainline-consolidation plan at the top of this file.

## What W170 changed

- Windows already used the shared authenticated `POST /api/v1/uploads`; the endpoint was not replaced.
- MP3 local duration preflight now recognizes the bounded leading ID3v2 / Info-Xing / APEv2 / ID3v1 metadata variants accepted by the extension/server cleanup.
- Local inspection is read-only: no cleanup, rewrite or transcoding in Windows. The original selected bytes go to the server unchanged.
- Upload success requires HTTP **202**, `status=pending`, and a positive `replacement_id`; generic 2xx or malformed bodies are not success.
- Clear errors are shown for `invalid_mp3`, `invalid_m4a`, `upload_too_large`, and missing server confirmation.
- Existing 30 MiB limit, 1.5-second duration tolerance, rights declaration, request ID/deduplication and in-flight duplicate-submit guard remain.
- The deployed server remains authoritative for metadata cleanup, duration measurement and full audio decode. **Do not redeploy server code.**

## Verification and delivered package

All checks for the built source passed on 21 November:

- Main CI [44887076540](https://github.com/manufact-test/nomusic/actions/runs/44887076540) — SUCCESS.
- Windows integration CI [44887076485](https://github.com/manufact-test/nomusic/actions/runs/44887076485) — SUCCESS.
- W20 safe internal installer staging [44887071981](https://github.com/manufact-test/nomusic/actions/runs/44887071981) — SUCCESS.
- W15 native contract: **467 passed**.
- W23 native tests: **156 passed**; W24 image-builder: **20 passed**; W21 recovery contract: **41 passed**.
- GUI and supervisor warning-as-error builds, PE/version/anti-downgrade validation, disposable per-user install/uninstall, package and checksum checks all passed.

The owner was already given these files in the previous chat:

- `CELIKOM-W170-WINDOWS-UPLOAD-CLEANUP-02452-UNSIGNED.exe`
- `CELIKOM-Windows-0.24.52.zip` (contains exactly one root EXE, byte-identical to the standalone installer).
- Installer SHA256: `4a5c75bc70a936acfbc6af0c1c9d03281921203afce75b5fed55473a7ef59dc7`
- ZIP SHA256: `edd505333e400f0ef5da3d0c0aff3983b14255979cb5eb0f4d6fb7c7f5e67a4c`
- GitHub Actions artifact ID `14700675953`, run `44887071981`; expires **1 December 2026, 08:58:05 UTC**.

This is one internal unsigned owner-review build, not a production release. No signing, public feed or server deployment.

## Owner runtime follow-up — superseded by W173

The original W170 handoff was waiting for real-file testing on 0.24.52. Subsequent owner testing moved to W172/W173 and official Yandex 5.128.0.

- The owner confirmed Yandex 5.128.0 works and several real songs reached the moderation queue.
- Five new submissions were inspected at the stored/canonical-file level; later widened read-only audit covered all **13** post-activation uploads.
- Run [44895271863](https://github.com/manufact-test/nomusic/actions/runs/44895271863) verified **13/13** stored hash, size, duration, canonical-normalizer and full-decode checks; 9 approved, 4 pending, 0 failures.
- This does not identify which original files contained removable metadata because the audit reads files after server cleanup.
- Owner explicitly declined a per-song cleanup journal, removed-tag counters, extra telemetry and raw-file retention. Do not add these.
- Continue from the W173 current handoff; do not reopen the W170 work as a separate new task.

## Hard boundaries

Do not change playback, volume, Next/Previous, radio, VPN, audio routing, native Yandex host, Android, browser extension, auth/access, billing, moderation, or the already-deployed server. No speculative refactors or broad audits. Preserve the main backup and the current owner-accepted Windows line.


---

# CURRENT WINDOWS W169 (17 November 2026)

Read **`docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md`** before any other Windows history. Active source: UI `1ac135ba5312473cc6c7feca8d1f5f57726f5342`, native exception guards `b2f9131132e26020fd861dcb71d3c33b8ff9a0c1`. App **0.24.51.0**, native **0.24.32**, backup `backup/windows-w169-pre-track-handoff-crash-investigation-20261117` @ `92e0d9e63f5fd7dc7f243d7c2a2202cf5ad8b2de`. Owner says green status in 0.24.50 works; preserve it. No VPN modifications. **Actual Yandex restart mechanism not proven by old diagnostics; guards eliminate unsafe unhandled Node rejection/callback failure but runtime owner must confirm.**

---

# CELIKOM Windows — active W168 handoff (17 November 2026)

**W168 delivered for owner review:** W20 run `44051448677` SUCCESS; 0.24.50.0 owner installer/ZIP/SHA256 independently checked and verified in personal Library `/CELIKOM/W168/`. The Yandex spontaneous restart is STILL UNRESOLVED; see dedicated W168 incident doc. No audio/VPN/native module changes.

**CURRENT OWNER BUGS, not W167 stale instructions:** Read `docs/windows/W168-OWNER-THREE-ISSUES-20261117.md` FIRST. Owner has 0.24.49.0 and supplied two W54 diagnostics. W168 UI fixes committed at `2c352479b267266cd62fab7d8221bab97051c539` for (1) idle prompt after Start, (2) green available/paused labels without false audible claim. Proposed 0.24.50.0, native still 0.24.31. W168 backup: `backup/windows-w168-before-owner-three-fixes-20261117` @ `31e364bfba8795f84502f050d6716b2b6639f5cf`. **Third issue (actual Yandex main-process restart 08:13:54Z) diagnosed but root cause NOT proven; do not call it repaired or touch VPN/audio/host speculatively.** W167 documentation below is historical.

---

# CELIKOM Windows — active handoff W167 (16 November 2026)

**Status:** W167 UI fixes are committed on the W165-based branch. The single internal W20 owner-review package is being prepared; CI and owner runtime acceptance are still pending. W166 / 0.24.48.0 remains rejected and was not used as the implementation base.

## Exact repository state

- Repository: `manufact-test/nomusic`
- Product: **CELIKOM Windows only**
- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`
- W167 source checkpoint: `e88280740457bf539ec8e661416a26d9de1e1102`
- CI validation checkpoint: `8964ec124025cf2f480c0f913f5b7b2d69a90f00` (Main CI and Windows integration CI both succeeded).
- App version: **0.24.49.0**
- Native module: **0.24.31**
- Rollback branch before W167 fixes: `backup/windows-w167-pre-ui-fixes-20261116` @ `ea788eaed198b71db787215b9ba85829766d6062`
- W165 code baseline: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`
- Original pre-W166 backup: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`
- Main/W166 was not reset, force-pushed or modified by W167.

## W167 implementation

1. **Start / module refresh:** `StartAction` no longer clears `_compactStarting` before `ConnectYandexAsync`. The green Yandex connection banner remains visible through the existing module validation and upgrade. Startup completion is blocked while native integration is busy or the installed module still mismatches. If the initial consent prompt is declined, the banner is cleared. The real version check, upgrade, entitlement checks and fail-closed behavior remain intact.
2. **Transient waiting copy:** the fresh-heartbeat + `UNKNOWN` fallback now returns an empty track row. The same old waiting copy was removed from the legacy `_switchHint`, `_song` and service-status fallbacks. W164's 2.5-second previous-title/artist handoff, raw Track-ID suppression and pending-presence suppression are unchanged.
3. **Pause:** `Пауза` is neutral in both compact and legacy UI. The header connection dot/label still follow the independent fresh native-service heartbeat and may remain green.
4. **Active replacement:** the green predicate is centralized and remains strict: enabled bridge, fresh heartbeat, `ACTIVE_REPLACEMENT`, current `PLAYING`, `NATIVE_SOURCE_VERIFIED`, and approved presence. Mapping, HTTP 206, prefetch, entitlement or generic PLAYING cannot turn the label green. No W166 DOM observer was copied; no current W55 diagnostic was supplied to justify it.
5. **Spacing:** idle/disabled placeholder remains 18 px. Active status uses a 28 px row and 2 px lower gap before Account. No global window, title, artist or idle spacing changes.
6. **Scope:** no W23 native host/renderer, audio, VPN, source routing, server, auth, Android or browser-extension code changed.

## Verification and package — all CI passed

- Main CI: [run 43903409504](https://github.com/manufact-test/nomusic/actions/runs/43903409504) — **SUCCESS**.
- Windows integration CI: [run 43903409454](https://github.com/manufact-test/nomusic/actions/runs/43903409454) — **SUCCESS**.
- W20 safe installer staging: [run 43903271312](https://github.com/manufact-test/nomusic/actions/runs/43903271312) — **SUCCESS**.
- W20 source commit: `025a51d7478b3c7591f893a5dc55fd8ecfee7bdc`; it contains the full W167 source checkpoint above. Latest branch HEAD differs only by branch-scoped CI trigger configuration and this documentation update.
- W15 contract tests: `W15_NATIVE_CONTRACT_PASS 436`; W23 native tests and W24 native image-builder tests passed.
- W20 passed warnings-as-errors compilation, stage-only policy, PE file-version/identity and anti-downgrade validation, disposable install, same-AppId in-place upgrade, uninstall without touching Yandex, and one-installer ZIP/SHA256 checks.
- One internal unsigned owner-review package only:
  - Installer: `CELIKOM-W167-OWNER-UI-REGRESSIONS-02449-UNSIGNED.exe`
  - ZIP: `CELIKOM-Windows-0.24.49.zip`
  - SHA256 manifest: `SHA256SUMS.txt`
  - EXE SHA256: `f363a23b90a58268d31f2c5a34313f35510645ab34bcf2c9acfcc3521b14a852`
  - ZIP SHA256: `abd7ab026a6dcfa7532f4aa833c7db2c4bf93c81e76c17afa001b941dfa15f0e`
  - GitHub Actions artifact ID: `14242836055`; expires **26 November 2026, 16:06:19 UTC**.
- ZIP contains exactly one root installer, byte-identical to the standalone EXE. Both hashes were independently recalculated after download and matched the manifest.
- Verified Library files: `/CELIKOM/W167/` (installer, ZIP and SHA256 manifest). Use the Library copies for download, not a sandbox or direct Actions artifact link.
- Package is internal and unsigned; no production signing, public feed, deployment or owner acceptance is claimed.

## Owner manual check

1. Press Start with the module requiring refresh: green Yandex connection text appears immediately; no disabled-state copy or idle module-update hint appears during the operation.
2. Let Yandex open and press Next: no `Ожидаем воспроизведения в Яндекс Музыке…` flash; previous title/artist handoff remains stable and no raw Track ID or pending-presence copy appears.
3. When the current replacement is genuinely active, `Играет версия CELIKOM` is green only if exact current-source proof is present. If the owner hears the replacement but the label remains neutral, collect a fresh W54/W55 diagnostic from 0.24.49.0; do not weaken the proof gate.
4. Pause is neutral while the header connection indicator may stay green.
5. Active status-to-Account spacing is compact; disabled/placeholder breathing room remains.
6. No broad VPN/audio retest is required; those paths were accepted in W164 and remain untouched.

## Hard boundaries

Do not start from W166. Do not reset or force-push main. Do not alter audio, VPN, source routing, server, entitlement authority, updater architecture, Yandex files, Android or browser extension. No broad audits, speculative hooks or intermediate packages.
