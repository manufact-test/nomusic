# W119 — authoritative owner contract and CELIKOM Windows handoff

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
**Product:** the one existing CELIKOM Windows application  
**Working branch:** `main` only

> This document is the controlling handoff for the next developer/chat. Read it before changing anything. If any older W-series document, old release note, artifact name, or previous chat message conflicts with W119 or the top of `NEXT-CHAT.md`, W119 wins. Do not reinterpret the product model or invent another workflow.

## Status addendum — W124–W133, 14 November 2026

The product contract and owner task order in this document remain unchanged. The updater, source-evidence and elevation-audit status below has advanced:

- W124 connects the signed latest-manifest consumer, 30-minute scheduler, verified package staging, DPAPI transaction and W122 Supervisor READY launcher to the existing CELIKOM app. The final installer launch is bound to the exact signed journal transaction and reverified.
- W117's fail-closed initial LKG bootstrap remains present and is run asynchronously only when production trust is pinned and Yandex is idle.
- W125 invalidates the current-decoder witness and cached source evidence immediately when CDP detaches, so a stale decoder proof cannot keep the UI green.
- W126 removes the duplicate activation POST on first native install/upgrade. The consented install path uses the same bounded transient retry helper, retains the fresh access label and classifies network failure separately from native integration damage. W126 Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.
- W127 fixes a current-decoder/queue-identity event-order race. The native host retains bounded per-player CDP state and reconciles it after the current Yandex queue ID is observed. Green still requires a currently playing exact signed CELIKOM source for the same current track; mapping or HTTP 206 alone remains insufficient. The regression test proves late queue identity reconciliation, verified-only heartbeat, pending-recovery suppression and URL-free diagnostics. W127 Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) and Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.
- W128 audited CELIKOM elevation launch paths and added a Windows Integration CI guard. No explicit `runas`/administrator request was found in the reviewed app paths; the Inno installer remains `PrivilegesRequired=lowest` under `%LOCALAPPDATA%\Programs\CELIKOM`. The guard checks those launch/installer constraints and passed Main CI [43604761393](https://github.com/manufact-test/nomusic/actions/runs/43604761393) and Windows integration CI [43604761386](https://github.com/manufact-test/nomusic/actions/runs/43604761386) — **SUCCESS**. Exact pre-guard backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`; guard commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`. This still does **not** identify the external prompt the owner saw or prove it harmless. #53 remains OPEN pending the exact prompt publisher and owner Task Manager CPU/RAM/GPU evidence. See `docs/windows/W128-READ-ONLY-ELEVATION-LAUNCH-AUDIT-20261114.md`.
- W130 adds two URL-free CDP visibility signals: `PLAYER_CDP_PROPERTIES_SEEN` and `PLAYER_CDP_URL_PROPERTY_SEEN`. The owner TXT and automatic support snapshot now distinguish no player-property events from a Yandex build that exposes properties but not `kUrl`. The export explicitly warns that field visibility is **not** current-track or replacement proof; no source-selection/playback behavior changed. W130 Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) and Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**. Exact pre-W130 backup: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`; code/test HEAD: `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`. **#52 remains OPEN** pending actual owner-PC source acceptance. See `docs/windows/W130-SAFE-CDP-PROPERTY-VISIBILITY-DIAGNOSTICS-20261114.md`.
- W133 removes the stale-green window in the native playback status. When CDP invalidates the exact current decoder proof (source-left, not-playing, player destruction, current decoder error, or observer detach), the host immediately downgrades that track's heartbeat to neutral `NATIVE_MAPPING_ACCEPTED`, rather than waiting up to the next 2.2-second status sample. The local status cache follows the downgrade and rolls back if the heartbeat request fails; a later fresh signed-current-decoder proof can restore `NATIVE_SOURCE_VERIFIED`. No Yandex player control, source reload, queue, URL or audio behavior is changed. W133 runtime commit `d548ed0af0f3717669c1fbcd903fc4f626428c7e`; exact pre-W133 backup `backup/windows-main-pre-w133-immediate-source-witness-downgrade-20261114` @ `2958b9d03fdd803eaab2f20dfad3c9bb4c63d1d9`; test/current code-test HEAD `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`. Main CI [43608584535](https://github.com/manufact-test/nomusic/actions/runs/43608584535) and Windows integration CI [43608584562](https://github.com/manufact-test/nomusic/actions/runs/43608584562) — **SUCCESS**. **#52 remains OPEN** until the owner confirms actual audible replacement on «Ты»; CDP evidence is not speaker-level proof. No installer was built.
- W132 adds a regression-only VPN A→B sequence test after W131: the current decoder first leaves its previously verified CELIKOM signed source, then VPN state turns off and on, and a fresh authenticated resolve confirms no active replacement. The test proves there is no duplicate `QUALITY_CHANGE` reload, no subsequent replacement reload, and no loss of playing state or position. This complements W98's original-from-start no-reload test. Exact pre-W132 backup: `backup/windows-main-pre-w132-vpn-source-left-revalidation-20261114` @ `507052a14841ee08bf2ade513315618612130e8a`; test/current code-test HEAD: `c02cd4988292598f81e857062279d0179253a42a`. Main CI [43607847556](https://github.com/manufact-test/nomusic/actions/runs/43607847556) and Windows integration CI [43607847627](https://github.com/manufact-test/nomusic/actions/runs/43607847627) — **SUCCESS**. **#58 remains OPEN** pending owner-PC VPN A→B acoustic acceptance; no installer was built.
- W131 fixes a stale-mapping race after verified decoder source-left. The passive CDP callback is accepted only for the current track after it was previously proven to use the CELIKOM signed source; the renderer now invalidates that track's stale mapped marker before checking enabled state. A racing VPN/entitlement state-off therefore does not issue a redundant `QUALITY_CHANGE` reload after Yandex has already returned to original. If CELIKOM remains enabled, the existing bounded authenticated recovery path remains intact. W131 Main CI [43606490844](https://github.com/manufact-test/nomusic/actions/runs/43606490844) and Windows integration CI [43606490908](https://github.com/manufact-test/nomusic/actions/runs/43606490908) — **SUCCESS**. Exact pre-W131 backup: `backup/windows-main-pre-w131-source-left-map-invalidation-20261114` @ `9eb710d1227f56419d6e9f35b34b44b7941ef8ae`; runtime commit: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2`; test/current code-test HEAD: `2f41091d1af072483ed5c79782958002b0ee2101`. **#58 remains OPEN** until owner-PC VPN A→B playback confirms no audible pop. See `docs/windows/W131-VERIFIED-SOURCE-LEFT-STALE-MAPPING-INVALIDATION-20261114.md`.
- Current Windows code/test HEAD: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832` (W133 immediate decoder-witness status downgrade). W133 runtime commit: `d548ed0af0f3717669c1fbcd903fc4f626428c7e`. W127 implementation: `4fe42d745b6708524c65eb4f9855e026f314fefa`. Exact pre-W127 rollback snapshot: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`. Previous exact green W126 rollback remains `backup/windows-main-post-w126-ci-green-20261114` @ `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- Production feed origin, P-256 public key and Authenticode signer fingerprint remain intentionally empty. The updater is wired but dormant; no production update has been delivered or installed.
- All six owner issues remain OPEN. W125/W127 improve defensive source evidence, W126 improves first-install activation/retry, and W128 narrows the elevation audit; none proves audible owner-PC acceptance or closes #52/#53.

The priority order in section 6 and all one-product/main/backup/no-intermediate-installer rules remain authoritative.

## 1. Non-negotiable product model — do not change it

There is **one CELIKOM Windows product and one current version**.

- `main` is the actual product version. Develop, repair, integrate and maintain the application directly on `main`.
- `backup/*` branches are exact rollback snapshots of `main`, created before substantial changes. They are backups only; never develop on them.
- There is no Windows TEST product, no separate TEST version, no parallel QA product, no `experiment/*` development line and no second installer line.
- Never call `main` a test version. Never propose moving work into a test branch/product.
- Automated unit/integration tests and CI are ordinary engineering validation. They do **not** create a second product or version.
- Do not create or send intermediate installers. Finish the agreed work in the one main product first. Build one complete final EXE+ZIP only after the work and integrated checks are complete.
- Do not change the agreed architecture or start a replacement implementation from scratch.

The owner has corrected this several times. Treat it as a hard requirement, not a preference.

## 2. Exact repository state at this handoff

- Code baseline immediately before the W119 documentation-only update: `2c12ea50797d8c395e4a2e169c9000d897dffb11`. The current `main` also contains documentation-only W119 commits; always fetch live `main` before coding.
- Last Windows-specific implementation commit: `dafb6191a8e311053f64b455fec075f3944706f1` — W20 same-installer Supervisor allowlist/gate change.
- The current HEAD is a later repository-wide commit for a separate Android A1 diagnostic workflow. Preserve it; do not reset, rewrite or modify Android work.
- Exact backup of the code baseline before the W119 documentation-only update: `backup/windows-main-pre-owner-work-order-20261114` @ `2c12ea50797d8c395e4a2e169c9000d897dffb11`. Later W119 commits change documentation only, not application code.
- Main CI [43593559415](https://github.com/manufact-test/nomusic/actions/runs/43593559415) — **SUCCESS** at current HEAD.
- CELIKOM Windows integration CI [43593559384](https://github.com/manufact-test/nomusic/actions/runs/43593559384) — **SUCCESS** at current HEAD.
- Windows integration explicitly passed: W22/W23/W60 source/VPN/403/audio regressions; W21 recovery; W24 package/catalog checks; W15 login/native state; warning-as-error GUI and Supervisor builds; W114 same-installer Supervisor payload check; W20 installer stage allowlist; W110 watchdog simulation; W117 fail-closed trust/bootstrap checks.
- W118 live checks at code SHA `228a9d66cd2f858a537ce37a773fe65820a4e964`: Main CI [43592142890](https://github.com/manufact-test/nomusic/actions/runs/43592142890), Windows integration [43592142866](https://github.com/manufact-test/nomusic/actions/runs/43592142866), Stage 5 [43592142904](https://github.com/manufact-test/nomusic/actions/runs/43592142904), W90 inventory [43592142899](https://github.com/manufact-test/nomusic/actions/runs/43592142899), W98 reconciliation [43592142876](https://github.com/manufact-test/nomusic/actions/runs/43592142876) — all **SUCCESS**.

The current backup was verified against the exact current `main` HEAD before this documentation-only commit. No application code is changed by this handoff.

## 3. What is implemented and what that actually means

### Windows update/recovery infrastructure

W105–W118 added and CI-validated substantial pieces:

- Signed update trust and package verification, SHA-256 and Authenticode checks, rollback restrictions and no-autoplay safeguards.
- Durable DPAPI rollback journal and retention of verified previous/target installers.
- Independent Supervisor health witness and crash/rollback simulation.
- Exact signed payload identity, including app, native host, renderer and Supervisor.
- Schema-2 manifest generation and immutable per-version manifest/signature output.
- Initial LKG/bootstrap logic.
- Shared fail-closed trust configuration for GUI and Supervisor.
- W20 confirms that the existing Inno installer file allowlist contains exactly the existing app EXE, native `host.cjs`, native `renderer.js` and `CELIKOM.UpdateSupervisor.exe`.

**This is infrastructure, not a finished production updater.** Do not report the updater as ready just because these tests pass.

Still not complete:
- Production P-256 public-key pin, Authenticode signer certificate SHA-256 and official stable HTTPS feed origin are not provisioned. The production values intentionally remain empty.
- There is no confirmed live signed-feed publisher/atomic upload target.
- The main app has no completed signed `latest.json` consumer, trusted same-user Supervisor launch callsite, install coordinator, update scheduling and user notices.
- No real production-signed update, forced GUI crash, one-shot automatic rollback and owner-PC account/native/Yandex preservation test has run.

Never invent certificates, key material or an official feed URL. Never ask the owner to paste a private key or credentials into chat. When real production inputs are genuinely needed, request only the specific owner action that is necessary and use protected release configuration.

### Audio/gain server work W118

- W90 read-only inventory found 1,493 active approved replacements: one active nonzero-gain row (replacement 37 / Yandex track 40371622 / admin gain +11.5 dB), 1,492 zero-gain rows, no invalid gain values.
- W98 reconciled the existing private sidecar against exact replacement set, track/source version, admin gain, original source SHA-256, duration, source size, sidecar SHA-256/size, live entitled resolver identity and signed HTTP Range response.
- Existing sidecar passed signed Range HTTP 206 verification. The final run did not render a new audio file or insert a new sidecar row.
- Stage 5 audit passed its private snapshot, original media inventory and migration/schema invariants. The live database was not restored or rewritten. Original audio objects were not changed.
- Nine W98 exact-identity/TSV contract tests passed.

This closes the **server-side identity and delivery check only**. It does not close Windows listening behavior, gain loudness/headroom, seek, Next, crossfade, 403 recovery, VPN switching or the owner issues. Do not mark #56 or related audio issues closed based on this server proof.

### Installer packaging — important legacy trap

- W20 CI proves the **existing single installer definition** allows the app EXE, native host, renderer and Supervisor together.
- It does **not** prove an actual installer was compiled, installed or upgraded.
- No final Windows EXE+ZIP has been built or delivered at this handoff.
- The current Inno script still has historical metadata `AppVersion=0.24.36` and `OutputBaseFilename=CELIKOM-W100-WINDOWS-02436-INTEGRATED-QA-TEST-UNSIGNED`. This is legacy W100 naming, **not a second product or a direction to create a TEST build**. Do not build/distribute that stale artifact. When the one final package is eventually produced, set the correct current application version and normal product filename as part of that final main-line packaging work. Do not create an interim installer to test the name.

## 4. Owner's complete task list — preserve all items

These are the actual requested Windows tasks. Do not replace them with a newly invented roadmap or quietly drop one.

1. **VPN A→B and recovery:** reliable, fast reconnection; restore playback without long hangs, hiss or unexpectedly quiet audio.
2. **#52 — «Ты» (13 карат):** report replacement only when the alternate source is actually playing; eliminate false “replacement active” status.
3. **#53 — Brave/Windows performance:** diagnose and fix browser/system-wide freezes, CPU/RAM/GPU load and any elevated-rights/startup behavior related to CELIKOM + Yandex.Music.
4. **#54 — Big City Life:** fix the sudden mid-track volume drop.
5. **#56 — gain settings:** make admin gain apply consistently to intended tracks; verify actual loudness, clipping/headroom, seek, Next, crossfade and recovery.
6. **#57 — 403→206:** remove hiss/click/pop when an expired audio URL is renewed and playback resumes.
7. **#58 — original tracks:** prevent pops/cuts when VPN changes while original, non-replaced tracks or «Моя волна» are playing.
8. **First connection and startup:** fix first/second/subsequent launch, unsupported-version/server errors, connection initialization and recovery.
9. **Diagnostics:** keep diagnostics available after disconnect; make diagnostics usable and truthful.
10. **Autostart and tray:** correct Windows autostart, tray behavior, reconnect and recovery after failure.
11. **Yandex update detection:** check for new Yandex versions at least every 30 minutes, preferably faster; do not strand users waiting up to an hour.
12. **Automatic updater:** finish signed update verification, SHA-256, Authenticode and protection against substituted packages.
13. **Supervisor integration:** launch the independent Supervisor from the existing CELIKOM product; do not create another application.
14. **Automatic rollback:** on a failed new version, restore the previous working version once, preserving account/login, DPAPI data, native integration and user data.
15. **Production update delivery:** real signing keys/certificates, official HTTPS origin, signed manifests and reliable automatic delivery.
16. **Full integrated verification:** validate the fixes together, including update, forced failure, recovery, account preservation and uninterrupted/idle-safe Yandex behavior.
17. **One final package and rollout:** only after the work and checks above are complete, create one final EXE+ZIP from `main`; owner accepts it, then prepare the mass update. No intermediate installers.

### Current issue status

GitHub issues #52, #53, #54, #56, #57 and #58 were checked at handoff and are all still **OPEN**. Keep them open until the actual behavior is fixed and the relevant acceptance evidence exists.

- #52 source truth is not established by a UI status alone.
- #53 needs real performance/system behavior evidence, not only a successful compile.
- #54 needs the mid-track volume drop diagnosed and fixed.
- #56 server sidecar is verified, but Windows acoustic behavior remains unaccepted.
- #57 needs actual audio transition quality evidence.
- #58 needs original-source continuity during VPN changes.

CI passing is necessary, but it is not proof of audible/owner-PC acceptance.

## 5. How to continue — mandatory working method

1. Start from the exact current `main` HEAD above. Read this file, `docs/windows/NEXT-CHAT.md`, W118, W117, W101/W102 and the six open issues before changing code.
2. Work directly in `main`. Before every substantial code change, create an exact `backup/*` branch at the current `main` SHA. Verify its SHA. Never work on the backup.
3. Work in large, coherent blocks and continue through implementation, tests and documentation. Do not stop after every small patch to send a report or ask the owner to do manual work.
4. Do not change architecture or create new product/branch/build lines. Do not create or distribute intermediate installers.
5. Do not touch Android, browser extension behavior, original audio files or unrelated server logic while doing Windows work.
6. Do not ask for another email, password, token or random secret. Never put private signing material in chat or Git.
7. Do not claim a task is complete because a static guard or CI passes. Distinguish code coverage, live server evidence and actual Windows/audio acceptance.
8. Ask the owner for manual action only when it is genuinely impossible to verify without their Windows machine, listening or approved production input. Group those checks into one consolidated acceptance pass after the integrated work is ready.
9. Keep documentation current after each substantial block. Record exact commit SHA, exact backup, CI run IDs/results, what is actually proven and what remains open.
10. Keep reports short and infrequent: material changes, checks and blockers only. The owner asked for uninterrupted work, not a stream of progress messages.

## 6. Required order from here

- Continue fixing the complete owner task list in section 4 on the same `main` product. Prioritize the Windows playback/VPN/source/performance issues and startup/diagnostics/autostart behavior; do not package early.
- Complete the updater end-to-end in the same product: real trust provisioning, official feed, signed manifest consumer, safe Supervisor launch, install coordination, scheduling/notices, and real one-shot crash rollback with session/native/Yandex safeguards.
- Run the full integrated CI/regression suite and all feasible automated integrity/security checks.
- Only when the above implementation is complete, produce **one** final EXE+ZIP from `main` with the correct product version/name, verify hashes and in-place upgrade/session preservation, and hand that one build to the owner for the consolidated manual checks that cannot be automated.
- After owner acceptance, prepare the mass update. Do not mass-roll out before acceptance.

Do not substitute a partial QA package, a test product, a branch migration, or another “phase” that changes the agreed product model.

## 7. What the next chat should do first

Say only that you have taken over the existing CELIKOM Windows work. Read W119 and the authoritative top of NEXT-CHAT. Confirm the exact `main`/backup/CI state, then continue implementation in large blocks under the rules above. Do not ask the owner to repeat the task list. Do not propose a new TEST version, a separate QA branch, or an early installer.

