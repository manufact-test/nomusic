# W124 — Stable update coordinator, safe scheduling and Supervisor-gated install — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W124 code backup: `backup/windows-main-pre-w124-stable-update-coordinator-20261114` @ `e734579f0f6e6aff1436bbccdbc1396a055cb788`.
- W124 final code HEAD: `cd5d2bf623f368529e5efd16e3d95c813975ad8d`.
- Exact green rollback snapshot: `backup/windows-main-post-w124-ci-green-20261114` @ the W124 code HEAD.
- Main CI [43600704215](https://github.com/manufact-test/nomusic/actions/runs/43600704215) and Windows integration CI [43600704211](https://github.com/manufact-test/nomusic/actions/runs/43600704211) — **SUCCESS**.

## Changes

1. Added `StableUpdateInstallCoordinator`, the single stable update transaction. It checks the immutable production trust tuple first and refuses to run if any production pin is absent.
2. Added a 30-minute WinForms scheduler in `MainWindow.StableUpdate.cs`. It is started only when production trust is configured. Each check defers while CELIKOM bridge is enabled, Yandex is running, playback state is unknown, or another install/host operation is busy.
3. The coordinator obtains/verifies the signed last-known-good installer, polls the signed latest manifest using W123 equal-sequence/no-update semantics, downloads and verifies a newer package, then rechecks idle state after download.
4. It creates a DPAPI-backed transaction with byte-identical previous/target signed installers and existing account/session/native identity, launches the immutable signed Supervisor snapshot through W122, and waits for its READY handshake.
5. Only after READY does it advance `Prepared → InstallerStarted`, reverify the exact journal-bound target installer (SHA-256, Authenticode signer, manifest identity), and call the existing Inno AppId upgrade path. A launch failure is recorded as `ManualRecovery`; no unverified or unjournaled path can be executed.
6. Restored W117's asynchronous first-install LKG bootstrap call and method. It remains behind the same pinned production trust and Yandex-idle gates.
7. Added regression coverage for trust-unconfigured fail-closed behavior and the installer-started-to-manual-recovery transition. Windows integration CI also guards the coordinator, scheduler, Supervisor launcher, signed latest-manifest fetch and final signed-launch path.

## Safety boundary / what is not complete

- Production feed origin, P-256 public key and Authenticode signer certificate fingerprint are still empty by design. No real official delivery URL, key or certificate was invented.
- Therefore `TryGetProduction` returns false in this build: the scheduler does not start and the coordinator does no network or install work. **The updater is wired but not activated for production.**
- Still required: owner-approved official HTTPS feed, production P-256 public key, production Authenticode certificate fingerprint and protected release-side signing/publishing. Then run the real signed-feed install, forced-failure, Supervisor crash/one-shot rollback, account/session preservation and recovery tests.
- CI validates code and simulations only. No production installer was built; no owner installation or audible test was requested.

