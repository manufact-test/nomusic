# W112 — CELIKOM Windows exact signed installed-payload identity / 14 November 2026

> **W113/W114 extension:** before any production schema-2 feed was published, the contract was extended to four installed files. supervisorSha256 is now mandatory; the DPAPI journal stores previous/target hashes for the supervisor as well. The existing CELIKOM installer includes the helper. Implementation 5fbc5ed39694dbd43329d47e2ea169f4142cf540, packaging guard 273fe22132123d7af7d3e961748b9d09104c0c7a; Main CI 43579759654 / 43580005463 and Windows integration 43579759677 / 43580005419 all SUCCESS. Production signing/feed and helper launch remain OFF; see W113/W114 handoffs.

## Exact source, backups and CI
- Repository `manufact-test/nomusic`, only working branch `main`.
- Exact W112 code `a7dbed8e19c9f23d952f689c1074c6057d0116d0`.
- Main CI [43577376444](https://github.com/manufact-test/nomusic/actions/runs/43577376444) **SUCCESS**.
- Full Windows integration [43577376383](https://github.com/manufact-test/nomusic/actions/runs/43577376383) **SUCCESS**.
- Exact green backup: `backup/windows-main-post-w112-payload-identity-ci-green-20261114` @ same SHA.
- Pre-W112 backup: `backup/windows-main-pre-w112-signed-payload-identity-20261114` @ `3f2c528a9a3b01a1db6a76dcda84d8e466c724d2`.
- W112b pre-stager-guard backup: `backup/windows-main-pre-w112b-require-payload-at-staging-20261114` @ `d066efc937803ec1d0a1b6362de1883a6cf6c812`.
- Changed Windows code and Windows tests only. No Android, extension, Yandex original media, audio assets or unrelated server code touched.

## Why W112 exists
Before W112, the watchdog verified that the installed CELIKOM EXE had the expected PE version, publisher and Authenticode signer. That did not prove that the installed native bridge or renderer files belonged to the same release. A stale or replaced `host.cjs` / `renderer.js` could sit beside a correctly versioned EXE and still receive a healthy verdict.

W112 binds the installed application payload to the exact immutable release that was authenticated by the signed manifest.

## Signed manifest schema 2
`StableUpdateManifestVerifier.VerifiedRelease` now carries four separate payload digests, in addition to the installer's existing package `Sha256`:

| Manifest field | Installed file |
|---|---|
| `applicationSha256` | `%LOCALAPPDATA%\Programs\CELIKOM\CELIKOM.Companion.exe` |
| `nativeHostSha256` | `%LOCALAPPDATA%\Programs\CELIKOM\integration\host.cjs` |
| `rendererSha256` | `%LOCALAPPDATA%\Programs\CELIKOM\integration\renderer.js` |
| `supervisorSha256` | `%LOCALAPPDATA%\Programs\CELIKOM\CELIKOM.UpdateSupervisor.exe` |

- All four fields are mandatory, lowercase 64-character SHA-256 values.
- The manifest schema is now **2**. Schema 1 is rejected by the verifier because it cannot prove the installed payload identity.
- Existing package `sha256` remains the digest of the signed Inno installer. The four payload hashes are independent and represent the bytes installed from that package.
- `StableUpdatePackageStager.FetchVerifiedAsync` and `VerifyInstaller` both call the payload-identity guard. A package with a missing/invalid app, host, renderer or supervisor hash is not considered a verified installer even if its package hash and Authenticode signature pass.

## DPAPI journal schema 2 and supervisor
- `StableUpdateRollbackJournal.Record` stores eight hashes: previous and target versions of the app EXE, native host, renderer and supervisor.
- New `PrepareCore` / `PrepareSigned` transactions require all eight hashes before a rollback ticket can be written.
- The DPAPI journal reader can parse schema 1 for historical inspection when its other W111 checks pass, but schema 1 is not eligible for automatic mutation: `Advance`, `BeginRollback`, terminal health decisions and previous-installer authorization require schema 2. The W110 engine rejects schema 1 immediately.
- The W110 supervisor passes the target or previous version's four hashes to the health probe according to the current journal phase.
- `WindowsSupervisorHealthProbe` verifies exact bytes of `CELIKOM.Companion.exe`, `integration/host.cjs`, `integration/renderer.js` and `CELIKOM.UpdateSupervisor.exe`. The EXE must additionally pass Authenticode trust, pinned certificate fingerprint, exact PE version/company/product, and the running process path check. The probe then verifies authenticated local bridge response, W111 original-account DPAPI fingerprint and native integration identity.
- The same checks apply to the previous release after rollback. A correct version number or signer alone is no longer sufficient.

## Tests
- W15 tests sign schema-2 feed fixtures and verify all four returned payload hashes. They reject schema 1, malformed/empty hashes and invalid payload fields.
- W15 file-hash tests accept the exact four fixture files, then independently reject wrong/malformed hashes, missing files and tampering of EXE, native host or renderer.
- W15 journal tests prove a missing payload identity cannot create a rollback transaction and that all eight hashes survive DPAPI journal round-trip.
- W110 simulation rejects each mismatched app/host/renderer/supervisor payload hash and refuses schema-1 legacy journal records without payload witnesses.
- Windows integration also rebuilds the GUI and supervisor with warnings as errors, runs W15/W110 contracts and retains all W21/W22/W23/W24/W60 regression gates.

## Production blockers — do not misreport
W112 is code + CI, **not a released updater**:
1. The signed schema-2 manifest publisher/feed is not yet deployed. Existing public P-256 manifest key and Authenticode certificate fingerprint are not pinned into the production build.
2. W110's `ProductionSignerCertificateSha256` remains deliberately empty. CI proves that an unprovisioned helper exits code 3 before it can touch the journal or launch an installer.
3. Celikom.UpdateSupervisor is now included in the same CELIKOM.iss installer and built by the existing W20/Hostinger QA packaging paths. It is still not launched by the main application; it remains an internal helper of the same product, not a second user product.
4. That helper hash is now mandatory in the unpublished schema-2 contract. The remaining launch callsite and production signing trust must be completed before shipping.
5. No real signed Inno installer, killed-GUI update, real one-shot rollback, owner-device session preservation or Yandex-idle field test has been performed. Unit/simulation tests use synthetic payload files and fake probes/launchers.
6. No final signed EXE+ZIP, no interim TEST installer and no mass release. Owner-side VPN/audio/startup acceptance remains open.

## Next work order
1. W113 now implements deterministic schema-2 manifest generation and exact-byte P-256 signing, with a mandatory match against the client-pinned public key. It is not yet a live publisher: connect it to the approved secure release pipeline only after production key/certificate provisioning and official-origin confirmation.
2. Wire the real manifest public-key and Authenticode signer pins through approved production build configuration. Keep the helper fail-closed until both pins are real and independently checked.
3. W114 includes and hash-binds the supervisor in the existing CELIKOM installer. Next, wire its launch only through a trusted same-user private transaction copy after production pins are provisioned.
4. Run an end-to-end signed Windows fixture: normal update, force-kill the new GUI, wait for the bounded watchdog decision, close Yandex, perform exactly one verified restore, and prove the old app + exact payload hashes + bridge + DPAPI account + native integration all recover.
5. Then owner QA: VPN A→B, «Ты», Big City Life volume, 403→206/no hiss, «Моя волна» originals on VPN switch, Brave/Windows resource usage, startup/reboot and diagnostics. One final signed EXE+ZIP only after all gates pass.

