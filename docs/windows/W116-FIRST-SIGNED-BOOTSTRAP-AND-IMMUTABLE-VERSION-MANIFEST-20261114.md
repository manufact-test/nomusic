# W116 — first signed-install bootstrap and immutable version manifest

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
Product line: `main` only

## Source, backups and CI

- Exact verified code/test HEAD: `d1c807dbc2bb748a8a6d692ef0e01b96a5d9f7d5`.
- Main CI [43585155970](https://github.com/manufact-test/nomusic/actions/runs/43585155970) — **SUCCESS**.
- Windows integration CI [43585155942](https://github.com/manufact-test/nomusic/actions/runs/43585155942) — **SUCCESS**.
- Exact pre-W116 rollback: `backup/windows-main-pre-w116-first-signed-bootstrap-20261114` @ `f5239fccb7f9dd1bd2789f8f2eb9849b91b5ab71`.
- Additional exact checkpoints: `backup/windows-main-pre-w116-bootstrap-test-scope-fix-20261114` @ `0f16c51afd48ee56b25d2f8d50e586c3dd985963`; `backup/windows-main-pre-w116-nullability-fix-20261114` @ `5be0e24ac3c778839693563554dfa19cd5907cc0`; `backup/windows-main-pre-w116-installed-app-identity-adjustment-20261114` @ `929b2ccd274bc403b9cb1601309d0feb40c2d2be`.

## Why W116 exists

W115 can reuse the last verified target package after a completed signed update, but a clean first signed installation has no previous transaction journal and therefore no LKG package. W116 supplies that missing first-install seed without trusting the current unsigned/manual updater or treating installed files as an installer.

## What changed

### Immutable version-addressed release metadata

- `.github/scripts/windows-stable-manifest.mjs` now writes:
  - mutable discovery pointer: `latest.json` and `latest.json.sig`;
  - immutable per-version metadata: `{version}/manifest.json` and `{version}/manifest.json.sig`.
- Existing versioned metadata can be reused only when the document is byte-identical and its existing detached signature validates against the expected P-256 public key. A changed document, key or partial/symlinked pair fails with `W113_VERSIONED_RELEASE_IMMUTABLE`.
- The package itself remains a separate artifact. The release publisher must upload it at the exact immutable version path already bound into the signed manifest. This generator is not a live publisher.

### Exact-version bootstrap verification and fetch

- `StableUpdateManifestVerifier.VerifyBootstrap` verifies the detached P-256 signature, stable channel, publisher, package URL/origin, package size/hash and all four payload hashes.
- Bootstrap mode accepts only the exact version already installed and rejects rollback directives. It may accept an expired version-addressed immutable release record because it is used only to recover that exact installed version; normal `latest.json` offers still enforce expiry, monotonic sequence and forward-version rules.
- `StableUpdateManifestFetcher.FetchSignedVersionAsync` fetches only `/CELIKOM/Windows/Updates/stable/{version}/manifest.json` and its detached signature. It keeps exact-origin HTTPS, bounded response sizes, no redirects, no cookies and no default credentials.

### First LKG seed

- New journal phase `Seeded` is a completed bootstrap state, not an update transaction. The record uses a strict `0.0.0.0` / sequence-0 sentinel for the nonexistent previous version and stores the exact signed current release as its target.
- `SeedInitialLastKnownGoodSigned` verifies the installer SHA-256, Authenticode trust, pinned signer certificate and CELIKOM PE version. It also checks the exact currently installed hashes for:
  - `CELIKOM.Companion.exe`;
  - `integration/host.cjs`;
  - `integration/renderer.js`;
  - `CELIKOM.UpdateSupervisor.exe`.
- It copies the verified installer into the user-scoped rollback vault, verifies the copy again, and writes the DPAPI journal only after the four installed payloads still match. Existing, pending, corrupt or untrusted journals are never overwritten.
- `StableUpdateBootstrapper.EnsureInitialLastKnownGoodAsync` first reuses an existing verified LKG. Only when the journal is genuinely absent does it fetch the immutable manifest for the running version, download and verify that signed installer, seed the journal, re-read the LKG and clean the temporary download.
- The bootstrapper does not launch an installer, restart CELIKOM, access Yandex or interrupt playback.
- `GetLastKnownGood` accepts `Seeded` and returns the target package. The first subsequent signed update can use that exact package as its previous installer. The seed snapshot is removed only after the next transaction has copied and verified both packages and durably written its own DPAPI journal.
- The independent Supervisor treats `Seeded` as a completed state; it is not a live rollback transaction.

## Regression coverage

W15 tests cover:

1. Exact-version immutable bootstrap manifest accepted even after its offer expiry.
2. Wrong installed version and rollback directives rejected.
3. Versioned manifest fetch requests only the exact `manifest.json` and `.sig` paths.
4. Installed-payload mismatch prevents seeding.
5. Duplicate bootstrap cannot overwrite an existing journal.
6. Seeded package is returned as the exact current LKG and reused as the first update's previous installer.
7. The first update removes the seed snapshot only after its new transaction is durable.

Main CI also passed the JavaScript manifest-generator tests, including immutable versioned metadata and refusal to rewrite a changed release. Full Windows integration passed the existing W22/W23/W60 audio/VPN/403 suite, W21 recovery, W24 catalog/ASAR checks, W15 contract tests, warning-as-error GUI and Supervisor builds, W110 watchdog simulation, W114 single-installer packaging guard and W108 no-autoplay updater checks.

## Still blocked — no automatic updater is enabled

- Production P-256 private key, client-pinned public-key DER and Authenticode certificate SHA-256 fingerprint are not provisioned. `ProductionSignerCertificateSha256` remains empty; the Supervisor intentionally refuses to launch.
- Official production HTTPS feed origin and atomic upload destination are not confirmed. Do not assume the Hostinger QA hostname or `celikom.com` is the production feed.
- W116 bootstrap code is **not wired to MainWindow/startup** until the real trust pins and official origin are provisioned.
- The main app still has no trusted same-user Supervisor launch callsite or complete signed latest-manifest/stage/install orchestration.
- No real production-signed installer/feed, forced GUI crash, automatic one-shot rollback, owner-PC account-preservation or Yandex-idle test has run.
- No final EXE+ZIP has been built or delivered. No mass release.

Do not paste private keys into chat or commit them. Do not fill production pins with guessed values. Do not publish to the Hostinger QA hostname as a substitute for the official feed. Do not enable automatic installation until the actual signed update/rollback path passes on Windows.

## Next

1. Provision production P-256/public-key and Authenticode trust through protected release configuration.
2. Confirm the official HTTPS stable-feed origin and atomic upload target; publish the immutable version package + manifest/signature and mutable latest pointer.
3. Wire `EnsureInitialLastKnownGoodAsync` into the existing CELIKOM startup only after trust inputs are real.
4. Wire the normal signed update flow and same-user Supervisor launch, then run a real signed update/forced-crash/one-shot-rollback test with Yandex closed and the existing account preserved.
5. Only after that produce one final EXE+ZIP for owner QA.

Keep the one existing CELIKOM Windows product, AppId, install path and main branch. Do not create test products or release intermediate installers.
