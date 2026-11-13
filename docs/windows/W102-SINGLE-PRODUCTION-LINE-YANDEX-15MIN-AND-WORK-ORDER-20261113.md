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

### Critical repository fact — reconciled

The Windows application source is now present on GitHub `main`. **`main` is the one canonical CELIKOM Windows production line.** The Windows source was integrated without merging the entire divergent experiment history or overwriting Android, extension and server work.

Current canonical HEAD at this update: `8a4d7ef1ed0e1551119c466a1c805dc5dc7c2c1e`.

Exact safety backups:
- Original repository `main`: `backup/windows-main-pre-w102-handoff-20261113` @ `2741c403772f6e2837cd27bf748f90dc8d7722c9`.
- Original Windows source snapshot: `backup/windows-source-pre-w102-handoff-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.
- Immediately before W53 diagnostic-retention changes: `backup/windows-main-pre-w53-incident-retention-20261114` @ `cc19eec9a8d7e54bfb8a989f52266d5b4e028f08`.

**Current rule:** continue all product changes directly on `main`, create only exact `backup/*` rollback points before substantial changes, and do not revive old `experiment/*` branches as active product lines.

## 2. Yandex Music vendor update monitoring — change hourly to 15 minutes

### Current verified state

The workflow remains at `.github/workflows/windows-yandex-hourly-release-watch.yml` for compatibility, but its display name and schedule now say **15-minute monitoring**. The schedule is `7,22,37,52 * * * *`.

Implemented on `main`:
- Discovery and long candidate verification use separate concurrency groups; a slow candidate check no longer blocks the next discovery cycle.
- A newly detected release is reported immediately while signature/EXE/ASAR validation runs separately.
- Both workflow checkout refs now use `main`; the stale W81 experiment-branch dependency is removed.
- The reviewed compatibility feed URL now points to the catalog on `main`.
- CELIKOM checks Yandex on startup. A scoped file watcher detects changes to the installed Yandex EXE or `app.asar`, debounces the event, and forces a catalog refresh that bypasses the normal 15-minute cache.

CI evidence: [43516252084](https://github.com/manufact-test/nomusic/actions/runs/43516252084) and [43516252338](https://github.com/manufact-test/nomusic/actions/runs/43516252338), both SUCCESS.

Still required: add/verify an immediate compatibility recheck specifically after a native bridge/start failure. A signed Yandex installer alone does not prove runtime/audio compatibility; unknown versions must fail closed.

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
| 3 | #53 Brave/Windows freezes and excessive load | W92 passive event-loop stall and memory signals existed, but W53 found they were not classified as incidents by the durable archive or support-snapshot priority filter. Fixed in `8a4d7ef`: both signals now survive noisy polling in the 7-day incident archive and support snapshot; owner TXT includes explicit stall/memory summary fields. Main CI [43518322767](https://github.com/manufact-test/nomusic/actions/runs/43518322767) and full Windows integration CI [43518322776](https://github.com/manufact-test/nomusic/actions/runs/43518322776) both SUCCESS. No audio/CDP polling behavior was changed. | **Partial; code + CI proven.** Need the owner's diagnostic from the next accepted build and one safe Task Manager snapshot of Yandex/CELIKOM/Brave CPU, memory and GPU at the slowdown. Elevated-rights prompt source remains unidentified; do not assume it was CELIKOM or harmless. |
| 4 | #54 Big City Life suddenly becomes about half as loud mid-track | Passive source/volume observer and bounded recovery exist. Owner reports alternative keeps playing quietly; exact cause/event is not captured. | **Open.** Reproduce and identify whether gain metadata, served bytes, player normalization, Windows audio session or source transition changes mid-track. Do not conflate with #56. |
| 5 | #56 Windows must apply admin gain to all active alternatives with nonzero `gain_db` | Windows-only private pre-rendered sidecar path exists. Previous live gain stage 43495186951 staged replacement 37 / track 40371622 at +11.5 dB; measured +6.70 dB RMS with peaks limited to 0 dB; signed Range 206 and `gain_applied=true` passed. Follow-up Stage 5 run [43514995243](https://github.com/manufact-test/nomusic/actions/runs/43514995243) passed: 1498 original audio objects matched SHA256, isolated MySQL restore recovered the Big City Life sidecar, and external HTTPS health/config plus anonymous-denial checks passed. | **Server recovery + sidecar preservation proven; field audio QA open.** Confirm actual Windows playback, headroom, seek, Next, crossfade and 403 recovery. Re-audit live inventory before further staging. Never alter browser-extension originals or original audio files. |
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

- Canonical production branch: `main`; current HEAD: `8a4d7ef1ed0e1551119c466a1c805dc5dc7c2c1e`.
- Code baseline: GUI 0.24.36 / native 0.24.29 / W23 package 0.24.10. The W53 change only improves diagnostic retention; it does not change audio playback or package versions.
- Latest exact pre-W53 code backup: `backup/windows-main-pre-w53-incident-retention-20261114` @ `cc19eec9a8d7e54bfb8a989f52266d5b4e028f08`.
- Original Windows source snapshot: `backup/windows-source-pre-w102-handoff-20261113` @ `0158fcf71d06e4784751b8ddc1982e2b951b2753`.
- Original default-main snapshot: `backup/windows-main-pre-w102-handoff-20261113` @ `2741c403772f6e2837cd27bf748f90dc8d7722c9`.
- Main CI [43518322767](https://github.com/manufact-test/nomusic/actions/runs/43518322767): SUCCESS on `8a4d7ef`.
- Full Windows integration CI [43518322776](https://github.com/manufact-test/nomusic/actions/runs/43518322776): SUCCESS on `8a4d7ef`, including W23 audio/network regressions, W24 catalog/ASAR tests, W15 entitlement/login/native-state tests and warning-as-error GUI compile.
- Stage 5 server recovery [43514995243](https://github.com/manufact-test/nomusic/actions/runs/43514995243): SUCCESS. Restore drill, all 1498 original audio SHA256 checks, isolated MySQL restore with Big City Life gain sidecar, external HTTPS health/config and anonymous-denial checks passed. Live MySQL was untouched.
- Earlier final release attempt [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358) failed at isolated MySQL restore and was not blindly repeated. The later Stage 5 run is a separate successful recovery/monitoring proof, not a final app release. No final EXE+ZIP has been delivered and nothing has been installed on the owner's PC.

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

1. Read W102, W101 and W100 and re-fetch the current `main` state before changes.
2. **Completed:** Windows source is reconciled on `main`; keep all further product changes on this single line.
3. **Completed:** Stage 5 restore/audit recovery passed in run 43514995243; live MySQL was not modified.
4. Continue the defect ledger in order. #52 false-green guard is in code/CI but needs owner audio proof. #53 diagnostic-retention fix is in code/CI but needs owner performance evidence. Proceed with #54 next; keep #54/#56/#57 separate.
5. Finish the missing immediate Yandex compatibility recheck after native bridge/start failure. The 15-minute monitor, main-branch catalog and local-version watcher are already integrated.
6. Close the remaining startup/diagnostics/autostart field checks without creating a second UI architecture.
7. Implement signed automatic CELIKOM updates and rollback inside the same application.
8. Produce one coherent next release, deliver it once to the owner, and enable mass rollout only after owner acceptance.
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
