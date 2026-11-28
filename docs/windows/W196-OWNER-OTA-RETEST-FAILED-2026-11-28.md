# W196 — Owner OTA retest still fails after 0.24.62 bootstrap route repair (2026-11-28)

## Owner result

The owner relaunched CELIKOM after W195 restored the public immutable 0.24.62 bootstrap files. The app still displays **0.24.62.0**. No 0.24.63 installation or update discovery is confirmed.

Fresh diagnostic:
- File: `Вставленный текст(20261128-101337).txt`
- Generated UTC: `2026-11-28T10:13:32.3268756Z`
- AppVersion: `0.24.62.0`
- NativeModuleVersion: `0.24.31`
- NativeModuleMatchesApp: `true`
- Current snapshot says `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`.
- Startup events:
  - `10:12:25.392Z STABLE_UPDATE_CHECK_FAILED`
  - `10:12:35.643Z STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE`
- No `STABLE_UPDATE_DOWNLOADED_WAITING_FOR_SAFE_POINT`, `STABLE_ROLLBACK_BOOTSTRAP_READY`, or installer-start event appears.

The two newly attached files are duplicate copies of the same 10:13:32 diagnostic, not independent before/after-Stop snapshots. The earlier 09:48:27 diagnostic predates W195. Do not claim a post-Stop diagnostic was captured. Do not ask the owner to repeat Stop solely for telemetry.

## Corrected W195 conclusion

W195 successfully restored the exact signed 0.24.62 immutable manifest, detached signature and installer to the existing public customer route. The maintenance run verified the route over HTTPS, full installer SHA256 and unchanged public 0.24.63 / sequence 10 latest pair.

However, the owner-device retest proves this server-side repair was **not sufficient**. The earlier statement that the missing 0.24.62 public files were the sole root cause was premature. Keep the W195 server repair; do not revert it. The actual client failure stage remains unproven.

The W196 attempt to inspect Nginx access logs through the one-time maintenance hook returned `FLOKI_MAINTENANCE_NO_PENDING_OPERATION`; no server command ran and no server state changed. The temporary request was cleared. Do not bypass this gate or attempt another maintenance action without authorization.

## Source findings

Exact 0.24.62 source commit: `0364309006bd3451778f01390398fe0f52e5a20c` (signed build run [45968594886](https://github.com/manufact-test/nomusic/actions/runs/45968594886)). The updater source has these relevant behaviors:

1. `MainWindow.Shown` starts `BootstrapStableRollbackIfConfiguredAsync` on a background task before `StartBridgeAsync`.
2. The bootstrap authenticates the immutable manifest for the currently installed version, downloads that version's installer, verifies all four installed payload hashes and seeds the local last-known-good (LKG) journal.
3. Separately, `CheckStableUpdateIfSafeAsync` runs the update coordinator. It authenticates the installed release, reads signed `latest.json`, downloads and verifies the newer installer, and only then can hand off to the Supervisor.
4. Both bootstrap and coordinator catch broad exceptions and export only generic `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE` / `STABLE_UPDATE_CHECK_FAILED`. The current diagnostic cannot distinguish HTTP, signature, installed-payload mismatch, local journal/DPAPI, staging or PE/hash failure.
5. After a failed update check, `_stableUpdatePendingSafePoint` remains false and the normal retry interval stays at 30 minutes. Pressing Stop does not trigger an immediate check. A 30-second retry is only selected after a verified update package was successfully downloaded and is waiting for a safe point.

This explains why Stop was not a useful test action after the failed startup check, but does not by itself identify the original exception.

## Owner-facing UX requirement (explicit)

- No manual Stop action is required for updates.
- Download and verify quietly in the background while CELIKOM is being used.
- Do not close Yandex or interrupt playback to install.
- Prefer installing at the next ordinary CELIKOM launch after the owner has naturally closed the app and Yandex. The update must not unexpectedly close an active CELIKOM session just because Yandex happened to exit.
- If an update is staged, preserve it across app close/reboot and resume installation automatically at the next eligible launch.
- No "download update" prompt, manual EXE download, or special user procedure.

The current implementation attempts to launch the installer as soon as its strict safe-point predicate becomes true while CELIKOM remains open. This differs from the requested next-launch UX and must be corrected before calling the updater customer-ready.

## Next engineering task

Repair the Windows updater as a focused workstream; do not touch the audio baseline, Android or browser extension.

1. Reproduce the exact 0.24.62 failure against the now-restored public routes using the exact signed manifest/package and the same .NET validation path.
2. Identify why the current-version bootstrap and update coordinator fail. Do not infer the cause from generic event names.
3. Add a bounded, privacy-safe failure classification to diagnostics (fixed allowlisted stage/reason codes only; never export URLs, tokens, signatures, exception text or user identifiers).
4. Fix the 30-minute retry behavior after transient failure, with bounded backoff and no busy polling.
5. Change installation scheduling to the explicit next-launch UX above. Persist a verified pending package and let the existing Supervisor perform the install only at the next eligible launch/exit boundary.
6. Add deterministic tests for missing/corrupt LKG, current-manifest HTTP/signature failure, installed-payload mismatch, latest-feed failure, pending package reuse, and next-launch install deferral.
7. Do not modify or re-sign the immutable 0.24.63 / sequence 10 release. Any new binary requires a new monotonically higher version and the existing protected production approval. Do not publish a new global release without explicit owner approval.

## Hard boundaries

- Preserve W195's restored immutable 0.24.62 public files.
- Keep public 0.24.63 / sequence 10 latest and signature unchanged.
- No manual installer detour unless the owner explicitly approves it after the automatic path is proven unrecoverable.
- No audio/runtime/Android/extension changes.

## Owner clarification and next-chat execution contract (28 November 2026)

The owner explicitly clarified the requested work after the failed retest:

- The goal is still to deliver the **already published 0.24.63 / sequence 10** to the existing installed **0.24.62.0**. Do not present this as a request to create another user-facing test version or a new update channel.
- Do not ask the owner to press Stop, close Yandex, repeat a launch, or send duplicate diagnostics as a substitute for engineering. The current diagnostic is already sufficient to establish that the client fails before any successful update download.
- The owner expects engineering changes to be completed and validated, then merged into the existing GitHub `main` workflow so the installed product can receive the resulting signed release through the existing protected approval mechanism. A short-lived internal code branch/PR is acceptable for safe development; it is **not** a new customer channel or a new product version for the owner to install manually.
- First priority remains recovering delivery of the already published 0.24.63 without changing its immutable package or sequence. Do not jump straight to a new release or rebuild 0.24.63.
- If the investigation proves a client-code change is unavoidable, make it on a short-lived branch from current `main`, add deterministic tests, merge the validated change to `main`, and only then prepare a new monotonically higher signed release using the existing protected GitHub approval. Read the authoritative release floor before selecting a version/sequence; 0.24.63 / 10 must remain immutable.
- Critical bootstrap question: if the installed 0.24.62 updater itself cannot fetch/install a later package, a fix inside a future binary does not automatically reach that installed client. Prove whether the failure can be repaired through the existing public route/metadata or whether a separate bootstrap is technically unavoidable. Do not conceal this dependency and do not perform a manual EXE installation without the owner's explicit approval.
- Compare the exact updater implementation in 0.24.62 source commit `0364309006bd3451778f01390398fe0f52e5a20c` with the already-published 0.24.63 source commit `9c6721fdb273fc0850213b79d339b0f47d3e83b0`. Reproduce the same signed manifest/package validation using the actual Windows/.NET code path; identify the precise failing stage before editing.
- Keep the agreed UX: background download and verification while CELIKOM is in use; never interrupt Yandex playback; never require Stop; persist a verified pending package; install automatically at the next ordinary CELIKOM launch after the owner has naturally closed CELIKOM/Yandex.
- No changes to W174 audio files, Android, browser extension, or unrelated backend. No more broad diagnostics-only loops. Keep user-facing updates short and action-oriented.

**State at handoff:** this continuation updated documentation only. No Windows runtime/updater source has been modified yet. The next engineer must continue the actual OTA repair, not report this documentation update as a code fix.
