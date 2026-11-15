# W150 — CELIKOM Windows owner-confirmed scope and strict sequential work order

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Product: the one existing CELIKOM Windows application  
Only working branch: `main`

## 0. Authority — read this first

This is the owner's latest explicit correction and work-order approval. It supersedes conflicting priority lists in older handoffs, including W139's earlier "automatic updater first" ordering and the commercial Authenticode/PFX requirements in W148.

W119 still controls the product architecture and working rules (one product, `main` only, exact backups, no Windows TEST product, no experimental development branches, no intermediate installers). W150 controls the current task scope and order.

**The developer must finish one task to code/test/CI-ready state before moving to the next. Do not hop between tasks, reopen unrelated old tickets, or invent extra work from the repository's historical OPEN Issues.** The owner should receive one consolidated build only after all agreed code work is complete.

> **Latest owner addendum — W157 (15 Nov 2026):** New live observations after the W154/W155/W156 work are recorded in [W157](W157-OWNER-FOLLOW-UP-VPN-PLAYER-UI-20261115.md). W157 is now the active, narrow follow-up and supersedes the old status below that only W154 owner acceptance remained. Work only the W157 items, in its exact order: Yandex close/lifecycle truth → VPN audio continuity → confirmed UI text/color/status corrections → diagnostics when supplied → focused tests/CI → one consolidated new build. Do not reopen the completed updater/P-256, autostart/tray or unrelated historical issues. The older W150 scope remains architectural/working-rule context, not permission to restart all earlier tasks.

## Current execution status — 15 November 2026 (historical status, superseded by W157)

- **Tasks 1–4 are complete at code/test/CI level** under W151–W154. They are not owner-PC accepted; the owner performs one grouped W154 acceptance using the single final package.
- **Task 5 is complete at code/test/CI level** under W155/W156: P-256 signed schema-2 manifest, SHA-256 package/payload verification, DPAPI transaction, independent Supervisor READY/health/one-shot rollback, protected release workflow and owner-package helper are in place. Do not reopen the runtime audit or add speculative code.
- Owner-side P-256 provisioning is complete. The private key is stored only in the protected GitHub Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM` in `windows-stable-production`; never request or expose the PEM.
- The one-shot marker was committed to `main`; after fixing canonical UTC expiry precision, protected release workflow run `43741752502` completed **SUCCESS** on source commit `bc59e0c7e4db749d616b318beb89369245811b44`. Main CI `43741752582` and Windows integration CI `43741752579` also completed **SUCCESS**.
- **The single final bootstrap package now exists:** Draft Release `celikom-windows-v0.24.38-owner-bootstrap`, release ID `446239144`, version `0.24.38`, sequence `1`. It contains exactly `CELIKOM-Windows-0.24.38.exe`, `CELIKOM-Windows-0.24.38.zip` and `SHA256SUMS.txt`. The ZIP helper verifies exactly one root EXE and matching content hash. The Actions artifact upload was skipped; the release remains an unpublished Draft.
- Exact backup before the final documentation update: `backup/windows-main-pre-final-release-docs-20261115` @ `bc59e0c7e4db749d616b318beb89369245811b44`.
- **Only remaining owner work:** download the single final package from the Draft Release, install over 0.24.37, and perform the one grouped W154 acceptance. No intermediate packages or further engineering tasks.
- DNS/TLS and production-feed publication remain deliberately deferred until infrastructure migration. Do not publish the Draft Release or production feed. Do not claim automatic production updates until DNS/TLS and the signed feed are live.
- No other task is authorized. Do not revisit Tasks 1–5, historical Issues, broad audits, unrelated code, Android or the browser extension. #52 remains open until owner-PC acceptance.
## 1. Exact repository baseline and backup

- Current `main` HEAD when W150 was authored: `0524158177beeedb50bff85d59ae573d90c19823`.
- Exact pre-W150 documentation backup: `backup/windows-main-pre-w150-owner-scope-handoff-20261115` @ `0524158177beeedb50bff85d59ae573d90c19823`.
- Owner's installed/last reviewed version remains CELIKOM Windows `0.24.37` (W138). No newer consolidated owner package has been delivered.
- Latest Windows runtime source before W148 release-pipeline scaffolding: W147 code HEAD `e174551dc086f8812f05840aa8e22d926889ad31`.
- Latest `main` CI at W150 baseline: Main CI run `43699852155` SUCCESS; Windows integration CI run `43699852121` SUCCESS. These are code/test results only, not owner-PC or audible acceptance.
- No new EXE/ZIP was built or delivered as part of W150 documentation correction.

## 2. Owner-confirmed task scope and order

### Task 1 — current Yandex player / CELIKOM UI synchronization and truthful source state

**This is the first active implementation task.** The owner observed these exact failures on 0.24.37:

- CELIKOM was closed and reopened while Yandex continued playing; the music played, but CELIKOM stayed at `Ожидаем` / `Идёт загрузка Яндекс.Музыки`.
- The alternate `Ты` (13 карат) played audibly, but CELIKOM showed stale `Зима` / CENTR and the false `Версия CELIKOM передана Яндексу` message.
- In Yandex `Моя волна`, a different song (owner identified the playing song as `Вечно молодой`) played while CELIKOM retained the previous track and transfer wording.
- After VPN reconnection, music played but CELIKOM said `Запустите трек в Яндекс Музыке` and failed to show the current song.

Required behavior:

- Reconcile the existing Yandex process/player on CELIKOM start/reopen and after reconnect; do not show startup instructions if Yandex is already playing.
- Current metadata must belong to the exact current player/queue/track identity, never a previous track, preload, previous session or late heartbeat.
- Distinguish playback state `PLAYING / PAUSED / STOPPED / UNAVAILABLE` from source `ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN`.
- `ACTIVE_REPLACEMENT` requires the existing exact-current-track + signed-current-decoder evidence. Mapping acceptance, URL transfer, HTTP 206, stale heartbeat or cache alone are not proof.
- Show `ORIGINAL` only when the current original source is actually identified. If not provable, show neutral `UNKNOWN`; do not guess.
- Immediately invalidate stale source/title/green/transfer wording on track change, stop, pause, player destruction, CDP detach, current-player switch or loss of current decoder proof.
- Never show `Версия CELIKOM передана Яндексу` as a claim of audible replacement unless the exact current decoder evidence proves it.
- Fix state reconciliation and event ordering, not a cosmetic timer or hardcoded text. Preserve the W127/W133/W134/W135/W141–W147 exact-evidence safeguards; do not weaken proof to make the UI greener.

Existing W141–W147 work already advanced this area, including current-player selection, queue/decoder reconciliation, explicit playback states, sequenced heartbeat renewal, stale-process retirement, audibility precedence and compact paused-state handling. **Do not restart from scratch.** Audit the current `main` implementation, close only genuine remaining gaps, add targeted regressions, run both CI workflows and prepare this task for the single owner acceptance build. Do not mark it owner-accepted until the owner checks the final build.

Tracking: Issue #52 is related to source-truth acceptance and stays OPEN until the owner's actual playback/source checks pass.

### Task 2 — VPN A→B audio artifact, while preserving the faster reconnect

Only the current owner-reported VPN issue is in scope:

- VPN A→B reconnect is now noticeably faster. **Preserve this improvement; do not regress to the old slow reconnect.**
- During the switch, owner hears a loud `пшик` / click / strange audio sound.
- Owner previously heard good/clean sound from the alternate `Ты` and the track he called `две гутыки`; do not rename that uncertain title.
- Crossfade sounded clean in ordinary listening without VPN; it still needs a VPN/recovery check.

Required engineering and regression coverage:

1. Trace the actual VPN route/reconnect/audio handoff and identify the cause of the audible transient before changing it.
2. Keep the existing faster A→B reconnection.
3. Cover separately: an active CELIKOM replacement during VPN A→B; an ORIGINAL track during VPN A→B; Yandex `Моя волна` during VPN A→B.
4. Check Next/crossfade after route recovery.
5. Avoid reloading/replacing an ORIGINAL stream when no CELIKOM replacement is active.
6. Do not modify original audio assets or unrelated audio-processing behavior.

Do not automatically expand this task into the old standalone #57 (403→206 signed-media recovery) or every historical #58 acceptance criterion. If code evidence proves a shared root cause, record the overlap and fix only what is necessary for the owner-described VPN A→B issue. Do not claim audible success from CI.

### Task 3 — Windows autostart and tray behavior

Existing code review already found:

- First launch calls `EnsureFirstLaunchDefault` and enables Windows startup by default.
- A deliberate user opt-out is persisted and must remain OFF.
- The app uses same-user startup (`HKCU Run`, `--background`); it must not demand administrator privileges or start Yandex/unauthorized playback automatically.

Work required:

- Verify the current implementation and add/fix code only if a real defect is found.
- Test first-install default ON, deliberate OFF persistence after restart and in-place upgrade, registry/menu agreement, X/tray behavior, and quiet background startup.
- Do not blindly reset an existing OFF choice to ON.
- Owner's actual machine state is not known until final consolidated acceptance.

### Task 4 — one consolidated regression pass and final acceptance preparation

After Tasks 1–3 are individually code/test/CI-ready:

- Review startup/reopen, existing Yandex reconciliation, current track/source transitions, stop/pause, VPN reconnect, tray/autostart and diagnostics after disconnect.
- Re-run the relevant Windows integration tests and both CI workflows on the final application source.
- Preserve the existing Yandex vendor-update detection cadence of 15 minutes; do not accidentally change it.
- Prepare one concise grouped owner test plan and confirm that the source is ready for the final release pipeline.
- **Do not build or deliver an owner installer yet.** No intermediate installer/package is allowed. The only owner EXE+ZIP is produced once, after the final P-256 updater work in Task 5 is integrated.

### Task 5 — automatic updater, P-256 trust and production feed (LAST ENGINEERING TASK)

The owner explicitly changed the order: complete the application fixes first; do the updater/key/release work only after Tasks 1–4 are ready.

Approved design:

- No commercial Authenticode certificate purchase.
- No company/legal-entity identity attached to CELIKOM for this purpose.
- Keep the existing Windows installation warning experience: if Windows shows the current unknown-app warning, the user can choose `More info → Run anyway`. Do not make this worse, do not suppress Windows security, do not ask users to disable Defender/SmartScreen/Smart App Control, and do not implement a security bypass.
- Use CELIKOM's own P-256 signed schema-2 update manifest. Embed only the public key in the client. Keep the private key outside the repository and out of chat/logs; store it in protected GitHub Actions secret/HSM for release signing.
- Verify exact product/version/sequence, signed manifest, package size and SHA-256, and all expected payload identities before staging/install. Authenticode is **not** a required CELIKOM updater trust pin in this approved design.
- Preserve the existing safe-point download/install behavior, independent Supervisor READY handshake, DPAPI transaction, account/session/settings/native integration and one-shot automatic rollback.
- Installed 0.24.37 has no production P-256 pin. Therefore a one-time trusted manual bootstrap is unavoidable: owner installs the one final coherent package containing the new public pin. After that, subsequent releases must be detected, downloaded, verified, staged and installed automatically without manual website downloads.
- Domain `celikom.com` is already purchased and is the fixed future production origin: `https://celikom.com`. DNS, TLS and public feed deployment are intentionally deferred until the product/infrastructure migration is complete. Prepare the code/config now, but do not attempt to publish to a non-existent HTTPS endpoint or change DNS early.
- W148's original scaffold contained PFX/Authenticode certificate/fingerprint gates. W155/W156 have now replaced that release path with the approved protected P-256 signed-manifest workflow. Do not restore or reintroduce the obsolete PFX/Authenticode gates.
- Prepare one safe local key-provisioning script for the owner to run once only if required by GitHub's protected-secret permissions. The approved helper is `.github/scripts/windows-stable-provision-key.ps1`: it uses built-in Windows PowerShell 5.1, Windows CNG, Notepad and the browser only; no Node.js, GitHub CLI, PowerShell 7, package manager, token or password is required. It creates the P-256 key locally with a user/SYSTEM-only directory ACL and opens the protected GitHub Environment page. The owner adds the PEM once as Environment secret `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`. Never ask the owner to paste or send the PEM in chat.
- Before migration, validate updater logic with automated/local fixtures only; do not claim production feed delivery. Test the updater end-to-end on the owner's PC only after the domain's DNS/TLS and signed feed are live: detect → download during playback → verify → wait for safe point → Supervisor READY → in-place install → health check → forced one-shot rollback test. Preserve account, DPAPI, settings, native integration and music continuity.
- Windows may still apply its own policy to unsigned executables. Keep the current warning experience; never promise that P-256 manifest trust creates a Windows-verified publisher or bypasses SmartScreen/SAC. If a particular Windows policy blocks execution, report it honestly; never ask users to turn protection off.

The W155 updater runtime and W156 protected release pipeline are implemented and code/test/CI-ready, but production updating is not yet operational: the owner has not provisioned the P-256 private key, no signed bootstrap EXE/ZIP has been built or installed, and DNS/TLS/feed migration is intentionally deferred. Do not call the updater production-live until those external steps are complete.

### Task 6 — build and deliver the single final owner package

Only after Tasks 1–5 are complete:

- Build exactly one coherent owner EXE+ZIP from `main`, with matching GUI/Supervisor/installer versions and hashes.
- Ensure the final package includes the P-256 public pin and the future production origin `https://celikom.com`; the updater remains safely dormant until the domain's DNS/TLS/feed is actually live.
- Deliver the one-time bootstrap package to the owner for installation over 0.24.37 with the same AppId. Verify account/session, DPAPI secrets, settings and native integration are preserved.
- The app remains safely dormant until migration activates DNS/TLS and the signed feed. Then verify a subsequent release updates automatically. No repeated manual downloads.

## 3. Explicitly excluded from this work order

Do **not** start, investigate, patch, or pull these in just because their old GitHub Issues remain OPEN:

- #53 — historical Brave/Windows freezes, resource usage and external elevation prompt.
- #54 — historical Big City Life mid-track volume drop.
- #56 — historical global gain_db/headroom/clip/seek/Next matrix.
- #57 — historical 403→206 signed-media recovery hiss.
- #58 — historical original/My Wave VPN interruption issue as a separate broad ticket. Task 2 is limited to the current VPN A→B audio transient described by the owner in W139.
- Any other old issue, audio feature, performance investigation or unrelated cleanup not explicitly included above.

These Issues must not be silently closed or deleted; they simply are not current authorized work. If a future owner test raises one of them again, obtain explicit scope before starting it.

## 4. Work protocol and reporting

- Work only on `main`; create an exact `backup/*` snapshot before each substantial code block.
- Keep one existing CELIKOM Windows product. No Windows TEST product, no experiment/development branch, no architecture rewrite, no unrelated Android/extension/server changes.
- Complete the current task end-to-end (implementation + targeted tests + CI) before starting the next task.
- Do not pause for tiny reports or ask the owner to test each intermediate patch. Do not build intermediate installers.
- Keep concise progress updates: task, actual code/test status, remaining blocker. Never claim done based only on CI.
- The updater/key/feed is the last engineering block; build the single owner package only after it is integrated (Task 6).
- The owner should not have to repeat the requirements in this document.

## 5. First message for the next chat

Copy the current first message from the authoritative top section of `docs/windows/NEXT-CHAT.md`. Do not use any archived first message in this file or older handoffs.
