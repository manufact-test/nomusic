# W109 — CELIKOM Windows durable rollback journal / 14 November 2026

> **Subsequent W110–W111 development:** a separately built internal watchdog and original-account DPAPI fingerprint now extend this journal. Green code @ `be6bda507aeeb68a7046a4ad12c41448d139860a`, CI `43575703455` and `43575703509` SUCCESS. See `docs/windows/W110-W111-INDEPENDENT-SUPERVISOR-SESSION-WITNESS-20261114.md`. **Production recovery is still OFF**, helper not bundled or signed; W109 statements below describe its historical implementation stage.

## Source and CI
- Repository `manufact-test/nomusic` — one active working branch `main`.
- Exact verified W109 code commit: `0d90fea82cfd8d95e7c830941e1443cafa594fd3`.
- Exact green rollback branch: `backup/windows-main-post-w109-rollback-journal-ci-green-20261114` @ same SHA.
- W109 prechange backup: `backup/windows-main-pre-w109-rollback-transaction-20261114` @ `2331a7de51c9ae2f33162bc382c77ad65bd34bb8`.
- Main CI [43572820346](https://github.com/manufact-test/nomusic/actions/runs/43572820346) **SUCCESS**.
- Windows integration [43572820294](https://github.com/manufact-test/nomusic/actions/runs/43572820294) **SUCCESS**.
- Changed files: `windows-companion/w15/Celikom.Companion/StableUpdateRollbackJournal.cs` and `windows-companion/w15/Celikom.Companion.Tests/Program.cs`. No audio, Yandex, Android, extension, server, UI or actual installer changes.

## Implemented: safe state only, no installation yet
- `PrepareSigned`: only accepts newer target than exact running version; target must have newer signed sequence and unexpired manifest; both previous and new installer must pass `StableUpdatePackageStager.VerifyInstaller` (SHA256, Authenticode, pinned signer cert, exact PE version). Before upgrade, copies the previous verified signed setup to a private immutable-by-convention per-transaction backup and checks the copied file again.
- The journal is stored per Windows user in DPAPI-protected `stable-update-rollback.dpapi`, with an atomic same-volume file replacement and a per-user exclusive lock. Snapshot uses a unique transaction id; the old snapshot is retained.
- Durable stages: Prepared → InstallerStarted → NewAppObserved → Healthy, or RollbackNeeded → RollbackStarted → Restored / ManualRecovery. Invalid/replayed transitions are denied; `Healthy` and `Restored` can **only** be confirmed by separate methods that require exact signed EXE, local bridge, preserved DPAPI session when expected, and matching native integration when previously installed.
- `Decide`: 10-minute bounded initial health window, then request rollback. A single rollback attempt is allowed; repeated rollback attempts lead to ManualRecovery rather than an install loop. `VerifiedPreviousInstaller` refuses an incorrect transaction/phase/pin or a modified signed rollback EXE, and reruns the full trust verifier immediately before any future launch.
- A later signed update may replace a **completed** Healthy/Restored journal, never a pending/failed/undecipherable one.
- W15 tests verify success/failure transitions, rollback timeout, missing health, no fake success, account/native preservation, one-attempt gate, tampered copied binary, corrupted encrypted record, overlap refusal and sequential 0.24.36 → .37 → .38 plan. Test-only `PrepareCore` uses a synthetic verifier seam; it is NOT a production signature witness.

## Explicit limitations / next work
1. No live call site invokes `PrepareSigned`; no independent watchdog process observes a new app crash. No automated recovery executable or installer launch is implemented. Journal alone cannot restore a broken application.
2. Production release-signing pinned public key and Authenticode certificate do not yet exist in published clients; signed live stable feed, signed final installer and end-to-end in-place/failed-install recovery tests remain blocked. DO NOT silently trust test-generated keys.
3. Need a separate runtime supervisor process that survives CELIKOM shutdown, consumes the DPAPI ticket, confirms new binary/bridge/DPAPI/native health by real read-only probes, checks current Yandex playback is inactive, re-verifies old signed setup before invoking one rollback, confirms restored application health and refuses further automatic loops.
4. Need bounded stable polling/notifications and no-playback-interruption install scheduling. Full W101 product policy remains authoritative.
5. Need owner's physical Windows audio tests for VPN reconnection and GitHub issues #52, #53, #54, #56, #57 and #58, start/diagnostics/autostart and final install/rollback. No final EXE+ZIP or mass release was produced.

No new secrets, account, email, working branch, parallel product or intermediate customer installer was created.
