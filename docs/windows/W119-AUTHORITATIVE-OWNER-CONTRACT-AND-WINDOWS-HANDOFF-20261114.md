# W119 — authoritative owner contract and CELIKOM Windows handoff

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
**Product:** the one existing CELIKOM Windows application  
**Working branch:** `main` only

> This document is the controlling handoff for the next developer/chat. Read it before changing anything. If any older W-series document, old release note, artifact name, or previous chat message conflicts with W119 or the top of `NEXT-CHAT.md`, W119 wins. Do not reinterpret the product model or invent another workflow.

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

