# W139 — CELIKOM Windows: owner acceptance feedback and automatic updater P0 — 15 November 2026

> **OWNER-APPROVED OVERRIDE — W150 (15 Nov 2026).** For the current work scope and order, follow `docs/windows/W150-OWNER-CONFIRMED-SCOPE-AND-SEQUENTIAL-WORK-ORDER-20261115.md` and the W150 section at the very top of `NEXT-CHAT.md`. W150 supersedes older priority statements below, including W139's earlier "updater first" ordering and W148's commercial Authenticode/PFX provisioning plan. Product architecture and main-only/one-product rules in W119 remain in force. Do not treat unrelated historical open Issues as owner-authorized work.

Repository: `manufact-test/nomusic`  
Product: the one existing CELIKOM Windows application  
Working branch: `main` only  
Owner-reviewed version: `0.24.37` (private, unsigned W138 package)  
Pre-W139 documentation backup: `backup/windows-main-pre-w139-owner-acceptance-handoff-20261115` @ `4ba4fab4313939afc45ef782dd5344b206d11286`

This document records the owner's first real listening/GUI feedback on 0.24.37 and explicitly changes the next-work priority. It supplements W119 and W101; it does not change the product architecture or close any existing issue.

## 1. Owner acceptance observations on 0.24.37

### Positive observations — retain these gains

- The owner reports the alternate CELIKOM version of «Ты» (13 карат) played and sounded normal. The level/boost also seemed correct by ear. **This is positive audible evidence, but not enough to close #52:** the UI simultaneously displayed stale «Зима» / CENTR and «Версия CELIKOM передана Яндексу».
- The owner separately reports a track referred to as «две гутыки» was playing the CELIKOM version with good sound and audible positive gain. The exact track title is not independently established; do not guess or silently rename it.
- Crossfade so far produced no obvious clicks/pops in the ordinary listening test. This is provisional only; repeat it during VPN A→B and recovery tests.
- VPN A→B reconnection is now noticeably faster than before. Preserve this improvement. However, the owner still hears a loud pop/hiss/strange audio artifact during the switch.

### Confirmed UI/source-state defects — one coherent high-priority workstream

The screenshots and owner observations show multiple inconsistent states while Yandex is already playing:

1. After CELIKOM had worked, was fully closed via the window X, then reopened and Start pressed, music played but CELIKOM remained at «Ожидаем» / «Идёт загрузка Яндекс.Музыки…».
2. While «Ты» (13 карат) was audibly playing as the alternate version, CELIKOM showed the unrelated stale track «Зима» / CENTR and «Версия CELIKOM передана Яндексу».
3. In Yandex «Моя волна», a different track (the screenshot shows «Вечно молодой») was playing, but CELIKOM continued to show «Зима» / CENTR and the old transfer message. The owner also reports stopping/changing a track that is not a CELIKOM replacement while the stale «Зима» information remained.
4. After VPN switching, the owner reported music playing (he mentioned Триагрутрика during this test), while CELIKOM showed «Ожидаем» and «Запустите трек в Яндекс Музыке», with no current track shown.

**Expected UI contract:**
- Current Yandex track metadata must be refreshed from the current player/queue, never retained from the previous track, preloaded track, or earlier session.
- The UI must distinguish current playback state (playing/paused/stopped/unavailable) from CELIKOM service/bridge state.
- Source must be one of ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN and bound to the exact current track and currently playing decoder evidence. A URL transfer, mapping, HTTP 206, old heartbeat or stale cache must not be presented as audible replacement proof.
- A current original or «Моя волна» track must never inherit the previous replacement title or «Версия CELIKOM передана Яндексу» message.
- On restart/reconnect, reconcile the existing Yandex process/player before displaying startup/loading instructions. Do not tell the owner to launch Yandex if it is already playing.
- On stop, pause, track change, player destruction, CDP detach, or lost source proof, immediately invalidate stale UI state. If the current source cannot be proven, show neutral UNKNOWN rather than stale green/transfer wording.
- Fix the state model and event reconciliation, not just a cosmetic timer or hardcoded label.

Relevant existing foundation: W127 current-decoder/queue identity reconciliation; W133/W134 immediate source-witness invalidation; W135 durable source-decision diagnostics; issue #52. Review the current renderer/host state flow before changing it. Do not weaken the exact current-track + signed-decoder proof.

### VPN/audio observation

- VPN A→B reconnect became faster, which is a regression-sensitive improvement.
- The owner hears a fairly loud «пшик»/pop and unusual sound while switching VPN during music. The track may be a CELIKOM replacement (owner was listening to Триагрутрика around this test; exact track/source not proven).
- Crossfade sounded clean in a non-VPN test, but has not been accepted under VPN switching.
- Next owner test must separately cover: replacement during VPN A→B; original track during VPN A→B; «Моя волна» during VPN A→B; then crossfade/Next after route recovery. Preserve the fast reconnect and avoid source reloads on original playback.
- Keep #58 OPEN. Do not assume all VPN pop behavior has the same cause as 403→206 recovery (#57).

## 2. Autostart — code review and required acceptance

Current source was inspected:
- `MainWindow.cs` calls `WindowsLaunchSettings.EnsureFirstLaunchDefault(Application.ExecutablePath)`.
- `WindowsLaunchSettings` enables HKCU Run on first launch by default, stores an `AutoRunConfigured` marker and preserves a deliberate user opt-out across later launches/upgrades.
- The command is `--background`; this is same-user startup and does not require administrator rights.
- `MainWindow.Autostart.cs` only resumes playback when the user previously pressed Start, account identity still matches and the server currently authorizes access. It does not launch Yandex automatically.

The owner wants **Windows startup ON by default**. The code appears to implement first-launch ON already; the owner's machine state is not visible to CI. Do not blindly override a persisted opt-out. During the consolidated acceptance:
- verify the tray/menu checkbox and actual HKCU startup entry agree;
- verify first install/default is ON;
- verify X closes/minimizes according to the existing tray contract and does not clear startup preference;
- verify a deliberate user OFF remains OFF after app restart and in-place upgrade;
- verify Windows sign-in starts CELIKOM quietly in the tray, without starting Yandex or unauthorized playback.

If the owner did not intentionally opt out and the setting is still OFF, diagnose the stored marker/registry synchronization and fix the actual cause rather than resetting preferences on every launch.

## 3. P0 — automatic CELIKOM application updates are mandatory

The owner explicitly states that automatic updating is a required product function: customers must not have to visit a website or manually download each new CELIKOM version. The owner expected the 0.24.37 build to download/install itself on his PC; this did not happen.

**Own the mistake:** W138 produced a private GitHub Actions EXE+ZIP artifact for manual owner acceptance. It did NOT deliver that artifact to the owner's PC through CELIKOM's automatic updater. Do not describe a private CI artifact or successful CI as automatic delivery.

### Exact current implementation state

- The local manual updater in `AppUpdateManager.cs` accepts a locally selected EXE/ZIP and stages it; it is not the normal automatic stable-feed flow.
- W124 added the signed latest-manifest consumer, 30-minute stable-update scheduler, package staging, DPAPI transaction and Supervisor READY launcher.
- `StableUpdateTrustConfiguration.cs` currently has empty constants for:
  - official production HTTPS feed origin;
  - P-256 manifest public key;
  - Authenticode signer certificate SHA-256.
- `TryGetProduction` therefore returns false. `MainWindow.StableUpdate.cs` exits before checking the feed; the scheduler does not perform automatic network download/install. This is why 0.24.37 did not download itself.
- W110–W124 Supervisor/rollback logic and CI simulations are not proof of a real production signed update or a real crash-triggered rollback on the owner's PC.
- W138 package was private and UNSIGNED. It must not be promoted to the public stable feed.

### Mandatory work order — first priority, not postponed

1. Re-read W101, W105–W118, W119, W124 and the exact current updater/Supervisor code. Re-fetch live `main`; do not rely on stale handoff SHAs.
2. Inspect existing release infrastructure, official domain/HTTPS availability, protected GitHub release secrets and any existing code-signing certificate configuration. Do not assume that owning `celikom.com` means a production HTTPS feed or certificate is ready.
3. Provision a real P-256 manifest signing keypair through protected release infrastructure; embed only the public key in the client. Never commit or request the private key in chat.
4. Provision/verify a trusted CELIKOM Authenticode code-signing certificate and pin its actual SHA-256 signer identity. Do not substitute a self-signed/untrusted or fabricated fingerprint for production.
5. Configure a real official HTTPS stable feed and atomic publishing of signed manifests/packages. Use monotonically increasing release sequence/version and exact payload identities already required by schema 2.
6. Connect the existing scheduler/coordinator to the real trusted feed. Verify manifest signature, HTTPS origin, package size, SHA-256, Authenticode chain/signer, product identity and exact app/native/renderer/Supervisor versions before any install.
7. Automatic background discovery and download must work while music is playing. Stage and verify safely; installation must wait for the existing safe point (Yandex idle / playback stopped or normal app exit) and must never stop Yandex, reset the bridge or interrupt a track.
8. Launch the existing independent Supervisor and require READY before installer execution. Bind install to the exact DPAPI journal transaction and target package.
9. Perform real in-place upgrade with the same AppId and installation path. Preserve account/session, DPAPI secrets, native integration, settings and user data.
10. Force a controlled failure after upgrade and prove one-shot automatic rollback to the last known-good package. Verify account/native/user data preservation and no endless rollback loop.
11. Deliver one coherent signed bootstrap build to the owner and verify the entire cycle on his PC: detect → download → verify → stage → wait for safe point → install → health check. Then verify a later update is fully automatic. Only after owner acceptance may the same stable feed be used for customers.

**Bootstrap reality:** the currently installed 0.24.37 binary has empty production trust pins and cannot trust a new signed feed. W101 already permits a one-time trusted bootstrap for a legacy/current installation; if required, explain that a single initial trusted upgrade may need manual delivery. After that, every subsequent release must update automatically. Never make users repeat the bootstrap or manually download every version.

If a real Authenticode certificate or approved official feed endpoint is missing, identify that as the exact external release blocker and request only the specific owner approval/action needed. Do not fabricate trust values and do not silently weaken the security contract.

Automatic updater completion is **P0 and a release blocker before general customer rollout**. Do not defer it until after unrelated polish. Audio/UI fixes continue in coherent blocks, but the updater must be completed and owner-tested before calling the Windows product ready for customers.

## 4. Remaining owner work — preserve open issues

The following have not been accepted/fixed by this listening session; keep GitHub issues #52, #53, #54, #56, #57 and #58 OPEN until their actual acceptance criteria pass:

- #52 — «Ты» (13 карат): audible replacement is encouraging, but stale/contradictory UI means current-track source attribution remains untrusted.
- #53 — Brave/Windows freezes, CPU/RAM/GPU and unknown elevated-rights prompt. W128 found no explicit CELIKOM runas path; exact external publisher and owner performance evidence remain unknown.
- #54 — Big City Life mid-track volume drop. The owner has not yet completed the dedicated full-track test.
- #56 — admin `gain_db` application across all relevant Windows tracks, actual dB/loudness, headroom/no clipping, seek, Next and crossfade. One/two positive listening observations do not prove global gain parity.
- #57 — hiss/click on expired signed audio URL 403→206 recovery. Not directly tested in this pass.
- #58 — original tracks and «Моя волна» during VPN A→B. A loud pop/odd sound is now owner-confirmed; quick reconnect is a positive improvement and must be preserved.

Also retain: first/repeated startup and reconnect, diagnostics after disconnect, tray/autostart acceptance, Yandex vendor update detection at the existing **15-minute** cadence (do not regress W102), and final integrated verification.

## 5. Current priority order for the next developer/chat

1. **P0 automatic CELIKOM updater** — provision real trust/feed, complete actual download/install/Supervisor/rollback and owner-PC cycle. This is mandatory.
2. **P1 UI/source-state synchronization** — restart, already-running Yandex, track changes, «Моя волна», stop/pause, VPN reconnect; eliminate stale track/source labels and false «Запустите трек» prompts.
3. **P1 VPN A→B audible recovery** — preserve the newly faster reconnect while eliminating loud pop/hiss/strange audio. Test original and replacement sources separately.
4. **Autostart/tray** — verify default ON and persistent user choice; repair only if actual code/registry behavior is wrong.
5. Continue #52/#53/#54/#56/#57/#58 and the remaining first-connection/diagnostics/vendor-update tasks; do not mark any issue closed without owner evidence.
6. One consolidated owner-PC acceptance after the coherent implementation. Retest «Ты», the track owner called «две гутыки», Big City Life, gain/headroom, crossfade under VPN, original + «Моя волна» VPN switch, 403→206, startup/tray and the full automatic update + forced rollback cycle.

## 6. Working rules

- Work only in `main`; one existing CELIKOM Windows product. `backup/*` are exact rollback points only.
- Before substantial code changes, create and verify an exact backup at current live `main`.
- No Windows TEST product, no experiment branch, no architecture rewrite, no intermediate installers and no mass release.
- Do not touch Android, browser extension, original audio assets or unrelated server code.
- Do not ask the owner to repeat the task list or manually check each tiny change. Group real-PC checks into one consolidated pass.
- Keep work moving in large coherent blocks. Send only concise material updates; do not stop after each small patch.
- CI is not audible acceptance and is not proof of production update delivery.
- Keep issues #52/#53/#54/#56/#57/#58 OPEN until proven.
- No new installer/package is needed just to update documentation. Build one next coherent owner package only when the integrated changes are ready.
