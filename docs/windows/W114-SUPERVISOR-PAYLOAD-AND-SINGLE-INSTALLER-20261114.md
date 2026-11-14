# W114 — CELIKOM Windows supervisor in the signed release payload and existing installer / 14 November 2026

## Source, backup and CI
- Repository: manufact-test/nomusic; one active product line: main.
- W114 implementation: 5fbc5ed39694dbd43329d47e2ea169f4142cf540.
- Exact pre-W114 backup: backup/windows-main-pre-w114-supervisor-payload-20261114 @ c7451d90863581794c70df7a3dc8c2525ee4930c.
- Packaging contract guard: 273fe22132123d7af7d3e961748b9d09104c0c7a.
- W114 implementation Main CI [43579759654](https://github.com/manufact-test/nomusic/actions/runs/43579759654) SUCCESS; Windows integration [43579759677](https://github.com/manufact-test/nomusic/actions/runs/43579759677) SUCCESS.
- Packaging-guard Main CI [43580005463](https://github.com/manufact-test/nomusic/actions/runs/43580005463) SUCCESS; Windows integration [43580005419](https://github.com/manufact-test/nomusic/actions/runs/43580005419) SUCCESS.

## Implemented
- Unpublished schema 2 now requires four installed payload SHA256 values: CELIKOM.Companion.exe, integration/host.cjs, integration/renderer.js and CELIKOM.UpdateSupervisor.exe.
- DPAPI journal schema 2 stores previous/target hashes for all four files. The supervisor engine refuses a journal without both supervisor hashes.
- Health probe verifies the installed helper's exact hash, Authenticode trust, pinned signer fingerprint and product version alongside the GUI and native payload.
- Supervisor process verifies its own running image against the previous helper hash and Authenticode signer before monitoring the transaction.
- Existing windows-companion/w20/installer/CELIKOM.iss includes the helper under the same {app} directory and AppId/product.
- Existing W20 and Hostinger QA build workflows build the helper before compiling that same installer. The integration CI statically checks the Inno entry, both build paths and the installed-helper smoke assertion.
- No second consumer app, alternate install path, test product or new working branch was created.

## Still blocked — do not call updater ready
- ProductionSignerCertificateSha256 is intentionally empty. The helper exits code 3 before journal access or installer execution.
- Production P-256 manifest signing key/public-key pin and Authenticode certificate are not provisioned.
- W113 generator does not publish a live feed. Official HTTPS origin and stable upload target still need confirmation; the Hostinger QA domain must not be assumed to be production.
- Main application still has no trusted callsite to copy and launch the helper from a protected same-user transaction directory after the signed journal is durable.
- No real signed installer, forced GUI crash, one-shot rollback, account-preservation or Yandex-idle end-to-end test has been run. No final EXE+ZIP has been built or delivered. The Hostinger QA installer workflow was not run.

## Next sequence
1. Provision the production P-256 key and Authenticode certificate through protected release configuration; pin their public identities in the shipping build.
2. Confirm official HTTPS origin and upload path, then connect W113 generation to atomic versioned publication using existing secure infrastructure.
3. Add the trusted main-app callsite: verify/copy the old supervisor to a protected per-transaction path, prepare the DPAPI journal, then launch only with the exact transaction GUID. Keep fail-closed until signer pins exist.
4. Run a real signed update, forcibly terminate the new GUI, prove one verified restore and preserve the original account, native integration and Yandex playback.
5. Only then produce one final EXE+ZIP for owner QA and later mass rollout.

## W114a — 14 November: preserve Supervisor hash in rollback re-verification

- Exact pre-change backup: `backup/windows-main-pre-w114-rollback-supervisor-hash-20261114` @ `ffb983ec97982263e4559b3d7e7aad120976ad76`.
- Fixed `StableUpdateRollbackJournal.VerifiedPreviousInstallerCore`: reconstructed signed previous-release identity now includes `PreviousSupervisorSha256`, in addition to application, native host and renderer hashes. The production verifier therefore validates all four installed payload identities when re-verifying the cached rollback installer.
- Strengthened the W15 synthetic signed-package verifier so rollback tests require all four payload hashes to be present. This specifically catches the omission that previously passed because the test seam checked only package bytes.
- Code commits: `54219d43e550e4c5ea42eb2fa511264a4255ee0e` and `a7c8474a9dadb55c55261bffe6e6141aabac1146`.
- CI for the final documentation HEAD is pending at handoff; do not claim W114a green until both Main CI and Windows integration complete successfully.
- This fixes rollback payload verification only. It does not provision production signing keys, launch the helper from the app, publish a live feed or enable automatic updates.

- Additional journal consistency guard: schema-2 `ReadRecord` now rejects missing/invalid previous or target Supervisor SHA-256 values immediately, rather than returning a record that only the engine later refuses. This aligns durable journal validation with W114's four-file payload contract. Code commit: `59a84955308ec73f3a4e3b8dad1282002eb4f3ed`.

- W114a regression coverage expanded: separate W15 cases now reject a previous release missing `SupervisorSha256` and a target release missing `SupervisorSha256`; this verifies both sides of the rollback pair fail closed before journal creation. Test commit: `0540673c68fdd2fca1bc32acda74496de6fe09e6`. Exact pre-test backup: `backup/windows-main-pre-w114a-supervisor-missing-hash-tests-20261114` @ `faf417f29db5a97cb4faded53663d07c4da64f1d`.
