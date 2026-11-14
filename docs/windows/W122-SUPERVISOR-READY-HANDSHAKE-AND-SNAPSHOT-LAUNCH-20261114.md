# W122 — Trusted Supervisor readiness handshake and immutable helper snapshot — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W122 code backup: `backup/windows-main-pre-w122-supervisor-handshake-20261114` @ `7d0d6e162e8a51c169db05fc232674d6de93f4d2`.
- W122 implementation commit: `7622b8034a47526547d406ed4ec5988afc0569b5`.
- Exact green rollback snapshot: `backup/windows-main-post-w122-ci-green-20261114` @ the W122 commit.
- Main CI [43598267910](https://github.com/manufact-test/nomusic/actions/runs/43598267910) and Windows integration CI [43598267928](https://github.com/manufact-test/nomusic/actions/runs/43598267928) — **SUCCESS**.

## Changes

1. Added `StableUpdateSupervisorHandshake`: a transaction-GUID named pipe restricted to the current Windows user.
2. The Supervisor first reads and validates the DPAPI journal, checks production trust and its own signed image, performs its first engine tick, then sends READY. It does not acknowledge an unreadable or unsafe transaction.
3. Added `StableUpdateSupervisorLauncher.StartAsync(record)`. It accepts only a schema-2 `Prepared` transaction with matching pinned signer and previous Supervisor hash; it copies the old signed Supervisor EXE into that transaction's immutable snapshot directory, starts it from there with the existing `--supervise <guid>` contract, and waits up to eight seconds for READY.
4. The helper runs from the snapshot copy, so the future installer can replace the installed `CELIKOM.UpdateSupervisor.exe` without locking the image that is actively monitoring rollback.
5. Added a stable journal snapshot-path helper and a Windows named-pipe handshake regression test.

## Safety boundary / what is not yet complete

- The future update coordinator must not advance `Prepared → InstallerStarted` or launch the signed installer unless `StartAsync` returns true.
- Production feed origin, P-256 public key and Authenticode signer fingerprint remain intentionally empty. The launcher returns false while production trust is unconfigured; no keys, URLs or certificates were invented.
- **This is the trusted launch bridge, not the completed automatic updater.** There is still no MainWindow/update-coordinator callsite that fetches a newer release, prepares the journal, launches the Supervisor and then starts the installer. That is the next implementation block.
- No installer was built and no user installation was requested.

