# W102 — CELIKOM Windows: single production line, Yandex monitoring, task ledger and rollout order

Date: 2026-11-13
Owner's explicit decisions from the latest discussion are authoritative.

## 1. Product and branch policy — one CELIKOM, one production line

The owner does NOT want a parallel TEST application, a second Windows product, or a stream of intermediate installers.

- CELIKOM Windows remains the existing original application.
- Every code change updates the one canonical Windows product line.
- Before any substantial code edit/release, create an exact backup branch pointing to the current known-good production commit. The backup is a rollback point, not a test version.
- Develop on the canonical production branch. Do not create `experiment/*`, `qa/*`, or user-facing TEST product branches for routine fixes.
- Internal CI and automated checks remain mandatory, but they are engineering gates, not another product or customer release channel.
- The owner receives one coherent next version of the same CELIKOM application, installed in place using the same AppId and install path. Preserve login/DPAPI, settings, autostart preference, Yandex originals and extension assets.
- No intermediate EXE/ZIP. No remote installation on the owner's PC.
- If the new version is bad, restore the exact previous production commit/package from its backup. Do not leave users on a broken release.

### Critical repository fact — do not ignore

GitHub default branch is `main`, but as of this handoff it does NOT contain `windows-companion/` or `docs/windows/`. The actual Windows application source and this Windows workstream are on:

`experiment/windows-w98-integrated-gain-and-original-vpn-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.

That branch descends from W95/W81 Windows work. GitHub compare reports the Windows branch and `main` as **diverged**, with thousands of commits in the comparison (main→W98: ahead 2661 / behind 41; main→W95: ahead 2556 / behind 41). This is NOT a safe simple merge. The Windows Yandex watcher currently present on `main` also checks out a separate W81 experiment branch.

Exact safety backups created before this handoff:
- Repository `main` snapshot: `backup/windows-main-pre-w102-handoff-20261113` @ `2741c403772f6e2837cd27bf748f90dc8d7722c9`.
- Current Windows source snapshot: `backup/windows-source-pre-w102-handoff-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.

**First engineering action:** reconcile the actual Windows source into the one canonical production line without overwriting Android, extension or server work on `main`. Inspect merge base, trees and Windows-only commits. Do NOT merge the entire divergent history blindly, do NOT reset `main`, and do NOT continue to treat an `experiment/*` branch as the permanent product line. Once a safe integration is proven, make the canonical Windows product live on `main` (or document the single agreed canonical branch if repository architecture makes that impossible). Retire all other working branches from active development; retain only exact `backup/*` rollback branches.

Do not modify code until the current source/backup relationship is understood.

## 2. Yandex Music vendor update monitoring — change hourly to 15 minutes

### Current verified state

The workflow on GitHub `main` is `.github/workflows/windows-yandex-hourly-release-watch.yml`.
Its current schedule is `19 * * * *`: **once per hour**, at minute 19. It deliberately avoids minute 0. The workflow checks out `experiment/windows-w81-vendor-monitor-compat-visibility-20261112`, not `main`.

Its behavior:
- Reads the official Windows Yandex release feed.
- Checks official installer Authenticode signature/publisher and the inner executable/ASAR identity.
- If the exact version is already in the reviewed compatibility catalog, reports it as supported.
- If a new version is detected, runs candidate validation and opens a review issue.
- A new build is NOT automatically added to the compatibility catalog; runtime compatibility review is still required.

Therefore current discovery can take close to an hour, and the watcher is tied to a stale separate branch. It is not acceptable as the final customer-support arrangement.

### Required behavior

1. Change official release discovery to **every 15 minutes**, not merely every 30. Suggested offset cron: `7,22,37,52 * * * *` (avoid the top of the hour). Keep manual `workflow_dispatch`.
2. Split the fast read-only discovery job from longer Windows candidate validation. A 25-minute validation must not block or queue the next 15-minute discovery cycle.
3. On a newly detected version, trigger candidate validation immediately in a separate workflow/job. Validate official installer signature, publisher, exact version, EXE/ASAR hashes, archive integrity and the existing native/audio contracts.
4. Add a lightweight client-side compatibility-feed check:
   - immediately at CELIKOM startup/network initialization;
   - immediately after CELIKOM detects that Yandex's installed version changed;
   - immediately after a native bridge/start failure that may be caused by a changed Yandex build;
   - with a bounded retry/backoff to avoid hammering the server.
5. The app should not wait for the next scheduled GitHub poll when it already detects a new local Yandex version.
6. Publish a compatibility catalog update as soon as the required checks pass. Unknown versions must fail closed; never trust a new version solely because its installer is signed. If automated runtime/audio validation cannot prove compatibility, alert the maintainer immediately and keep the previous known-good catalog entry.
7. Keep the monitor on the canonical production source line. Remove checkout dependencies on `experiment/windows-w81-...`.
8. Record detection time, candidate version, validation result and catalog publication time. The operational target is detection within 15 minutes under normal GitHub scheduling, with an immediate client-triggered check on local version change. GitHub scheduled jobs can be delayed; do not promise a hard real-time SLA.

**Important distinction:** 15-minute polling shortens discovery time; it does not magically make an unverified Yandex build compatible. The validation/catalog publication path must also be made fast. Do not bypass compatibility or subscription checks just to reduce downtime.

Related existing issue: #48 — preserve and complete Yandex vendor update monitoring after migration.

## 3. Complete Windows task ledger — reuse existing work, close each item

Status vocabulary:
- **Code + CI:** implementation is present and automated tests pass; owner-side behavior is still unconfirmed.
- **Partial:** some infrastructure/guards exist, but the reported problem is not proven fixed.
- **Open:** no complete implementation or no end-to-end proof.
- Do not use percentage estimates. Do not mark an audio issue fixed from CI alone.

### Main user-reported defects — keep exact separation

| Order | Task | Existing work/evidence | Actual status and closure condition |
|---|---|---|---|
| 1 | VPN reconnect after changing VPN takes ~40–50 seconds / drops audio | W89/W94 route-change debounce, stale request cancellation and fast authenticated recheck are integrated; Windows CI passed. Entitlement validation remains mandatory. | **Code + CI; field QA open.** Measure real reconnect on owner's PC and confirm no long interruption. Never bypass subscription. |
| 2 | #52 «Ты» — тринадцать карат shows green CELIKOM status but audible censored original | Source-witness / false-green guard and bounded current-track recovery are integrated; W89 diagnostics showed mapping alone did not prove the decoder used the alternative. | **Partial.** Must prove actual CELIKOM alternative is heard, not just mapped/prefetched/green. |
| 3 | #53 Brave/Windows freezes and excessive load | W92 passive event-loop stall, memory and source/volume diagnostics plus polling optimizations are integrated; tests passed. | **Partial.** Need actual owner diagnostic and CPU/RAM/stall evidence; identify and fix the real bottleneck. |
| 4 | #54 Big City Life suddenly becomes about half as loud mid-track | Passive source/volume observer and bounded recovery exist. Owner reports alternative keeps playing quietly; exact cause/event is not captured. | **Open.** Reproduce and identify whether gain metadata, served bytes, player normalization, Windows audio session or source transition changes mid-track. Do not conflate with #56. |
| 5 | #56 Windows must apply admin gain to all active alternatives with nonzero `gain_db` | Windows-only private pre-rendered sidecar path exists. Previous run 43495186951 staged replacement 37 / track 40371622, configured +11.5 dB; measured +6.70 dB RMS, peak limited to 0 dB; signed live HTTP Range 206 and `gain_applied=true` passed. | **Partial.** Latest run 43500415358 failed before repeating gain stage. Last audited active catalog: 1493 active versions, one active positive-gain row (Big City Life); one additional positive-gain row was disabled. Verify current inventory again. Then confirm actual Windows playback, headroom, seek, Next, crossfade and 403 recovery. Never alter browser-extension originals or original audio files. |
| 6 | #57 hiss/pop when audio recovers from 403 to 206 | Bounded 403 recovery guards and W22/W23 regression tests are integrated; CI passed. | **Partial.** Need real acoustic confirmation after natural recovery; do not force an artificial production 403. |
| 7 | #58 original songs / «Моя волна» pop or interrupt when VPN changes despite no replacement | Original/unknown source classification and no-reload behavior on VPN/entitlement transition are integrated; W22/W23 tests passed. | **Code + CI; field QA open.** Listen to original/non-replaced songs while changing VPN and prove CELIKOM is transparent. #58 is not #57. |

### Previously requested startup, diagnostics and reliability tasks

| Task | Existing work/evidence | Actual status and closure condition |
|---|---|---|
| First Start sometimes says unsupported version, second says server error, third works | W74 start-race guards and bounded retry integrated; CI passed. | **Code + CI; owner field check open.** |
| Diagnostics button disappears after transient network/server failure | W75 persistent diagnostic/incident history and permission-state correction integrated; CI passed. | **Code + CI; owner field check open.** |
| Startup popup flashes as blank/unstyled squares | W87 first-render/startup correction integrated. | **Code present; owner field check open.** |
| False red “CELIKOM module outdated / press Update” message when no such button exists | W87/W82 neutral actionable status and Start-based repair path integrated. | **Code + CI; owner field check open.** |
| Start CELIKOM with Windows quietly in tray by default; do not force-open Yandex | W87/W88 startup path integrated. Default ON; tray opt-out is remembered; explicit Stop remains authoritative. | **Code + CI; owner reboot check open.** |
| Safe native/Yandex repair after vendor update | W80/W81 verified vendor package identity and safe repair guards integrated. | **Code + CI; verify with 15-minute monitoring and a real vendor version transition.** |

Do not reopen already implemented items as new architecture projects. Inspect their existing code/tests and close only the missing end-to-end proof.

## 4. Current release pipeline and real state

- Current Windows source branch before consolidation: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.
- Code baseline: GUI 0.24.36 / native 0.24.29 / W23 package 0.24.10 at `e48e05f75629becc7efd2198dc7459a1ac91b825`; later commits in the current branch are documentation-only.
- Exact code rollback: `backup/windows-w100-handoff-pre-docs-20261113` @ `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- Exact latest source snapshot: `backup/windows-source-pre-w102-handoff-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.
- Exact default-main snapshot: `backup/windows-main-pre-w102-handoff-20261113` @ `2741c403772f6e2837cd27bf748f90dc8d7722c9`.
- Windows CI run [43500415302](https://github.com/manufact-test/nomusic/actions/runs/43500415302): SUCCESS on code SHA `e48e05f75629becc7efd2198dc7459a1ac91b825`.
- Hostinger/final package run [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358): COMPLETED / FAILURE at `Verify preserved data and restore new snapshot in isolated MySQL`. Private gain stage, final installer build and publication were skipped. Inspect exact logs and actual server state before any retry. Do not blindly redeploy, repeat migrations or advance the one-shot request.
- Prior run [43495186951](https://github.com/manufact-test/nomusic/actions/runs/43495186951) passed the live private gain sidecar stage for Big City Life with signed Range 206 and `gain_applied=true`. This is evidence for that one prior run, not proof that the latest run completed.
- No final 0.24.36 EXE+ZIP has been delivered from run 43500415358. No installation has been performed on the owner's PC.

## 5. Automatic CELIKOM application updates — required after core fixes, before mass rollout

Current source truth: `AppUpdateManager.cs` supports manual local EXE/ZIP selection and is staff/diagnostics-only (Ctrl+Shift+U). It is NOT a normal user-facing automatic updater.

Implement inside the same CELIKOM application:
- one official HTTPS stable manifest and immutable versioned packages;
- signed manifest with pinned public key and trusted Authenticode-signed installer;
- background discovery/download; verify signature, publisher, version, size and SHA256;
- update discovery must work even if the user is signed out or entitlement expired; it must not grant playback access;
- non-blocking notice and “Later”; installation at safe stop/exit only, never cut music or restart Yandex mid-track;
- in-place update with same AppId/path; preserve DPAPI/session/settings/autostart and Yandex/extension originals;
- independent post-update health check;
- local rollback to exact last known-good signed package if startup/health check fails;
- signed remote rollback directive naming exact bad source version and allowed known-good target; prevent downgrade/replay loops;
- retain current and previous known-good packages.

No private signing key in repository or normal CI logs. Until real code-signing and signed-manifest verification are configured and tested, do not enable unattended EXE execution.

### Owner bootstrap and mass rollout

1. Build one coherent next version of the existing app containing the finished fixes and updater.
2. Deliver that single version to the owner once for installation/acceptance. This is not a separate TEST product; it is the next version of the same CELIKOM.
3. The owner checks playback and the updater. Any bug is fixed on the canonical production line, with a backup first.
4. After owner acceptance, publish the signed stable manifest/package to the official update feed. Users with the updater-capable version receive future fixes automatically inside CELIKOM; no repeated website downloads.
5. Existing legacy installs that do not contain the updater need a one-time bootstrap update. Be honest about this limitation; automatic delivery cannot exist in binaries that have no updater mechanism.
6. Pause rollout or publish a signed exact rollback directive if a release regresses. Do not mass-publish a release before the owner has accepted it.

## 6. Required work order — no task hopping

1. Read W102, W101 and W100. Re-fetch all refs and workflow state.
2. Reconcile the Windows code source with repository `main`. Backups are already created. Do not blindly merge the diverged history.
3. Establish one canonical production branch and move all Windows work onto it safely. No experiment/test branches as active product lines.
4. Diagnose the exact MySQL restore/audit failure in run 43500415358 and establish actual server state before any retry.
5. Audit the existing implementation against the task ledger. Do not rewrite already-present code.
6. Close the seven main defects one by one in the listed order. After each issue: exact backup, targeted fix, relevant tests/CI, then update status. Keep #54/#56/#57 separate.
7. Close the startup/diagnostics/autostart items with one owner acceptance checklist; do not build another UI architecture.
8. Change Yandex discovery from hourly to every 15 minutes, split quick polling from candidate validation, add immediate client checks on startup/version-change/failure, and remove stale W81 branch checkout. Preserve signature/hash and runtime compatibility gates.
9. Implement signed automatic CELIKOM updates and rollback in the same application.
10. Produce exactly one coherent next release of the original CELIKOM. No intermediate installers and no TEST product label.
11. Owner installs that single version and performs one consolidated real-world acceptance pass. Fix any found defects on the same production line.
12. Only after acceptance, publish the signed stable updater feed for mass rollout. Verify a client actually discovers, downloads, validates, installs and rolls back a deliberately invalid package in a safe test environment before general availability.

## 7. Owner communication rules

- Do not ask for more emails, accounts, secrets, passwords or tokens. The existing owner-only GitHub secret preflight already passed.
- Do not install anything on the owner's PC.
- Do not say “fixed” unless the relevant closure condition above is met.
- Do not use arbitrary percentages. Report: done in code / CI proven / field QA pending / open.
- Do not make a long progress report. State the single current blocker and the next concrete action.
- Do not create a new branch just to have a new W-number. Backups are allowed and required; parallel product branches are not.
