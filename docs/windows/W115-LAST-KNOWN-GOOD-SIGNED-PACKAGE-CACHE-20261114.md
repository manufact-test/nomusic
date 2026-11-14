# W115/W115a — retained signed target package as the next last-known-good base

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
Product line: `main` only

## Source, backup and CI

- Exact code/test HEAD: `d74e61f68d8e12d3f2d1d56470e5f688b06b27e6`.
- Pre-W115 rollback: `backup/windows-main-pre-w115-last-known-good-cache-20261114` @ `779d916e889846ae29980aeacf7083cb4b59c12f`.
- Pre-W115a snapshot-rotation rollback: `backup/windows-main-pre-w115a-snapshot-rotation-20261114` @ `f6f0a68c520b8eb53ff4fb7474156381a22e1e5e`.
- Main CI [43583092781](https://github.com/manufact-test/nomusic/actions/runs/43583092781) — **SUCCESS**.
- Windows integration CI [43583092822](https://github.com/manufact-test/nomusic/actions/runs/43583092822) — **SUCCESS**.

## What changed

### W115 — retain the target package, not only the previous package

The signed rollback journal previously retained the previous signed setup but did not retain the target setup as the next update's future rollback base. That meant a later update had no durable current signed package to reuse.

- Added `TargetSize` to the DPAPI-protected schema-2 record. It is optional at deserialization so older schema-2 records remain readable; a legacy record with no target size is not eligible to seed an LKG package.
- `PrepareCore` now validates the target package size and sequence as well as the previous package.
- It copies both signed installers into the transaction snapshot:
  - `previous-signed-setup.exe`
  - `target-signed-setup.exe`
- Both copies are verified again after copying. The journal is written only after the two byte-identical package copies pass verification.
- Added `CachedSignedPackage` and public `GetLastKnownGood`. It returns:
  - the target package only after transaction state `Healthy`;
  - the previous package only after state `Restored`.
- Before returning, it checks the DPAPI record, expected signer fingerprint, package size/hash, version/sequence and all four payload hashes, then re-runs the production installer verifier (SHA-256, Authenticode signer pin and CELIKOM PE identity).
- The returned release metadata is local-cache metadata; its `.invalid` package URI is intentionally not a feed URL. Use the returned installer path and release identity as the previous package for `PrepareSigned`, never as a URL to download.

### W115a — bounded snapshot retention

- When a completed `Healthy` or `Restored` transaction is superseded, the next transaction first copies and verifies both the new previous package and target package, then durably writes its new DPAPI journal.
- Only after that write succeeds does it remove the superseded transaction snapshot.
- If old-snapshot cleanup fails, the new transaction remains valid and the leftover directory is harmless; cleanup never runs before the new journal is durable.
- This keeps one current rollback pair rather than accumulating two installer images for every release.

## Regression coverage

W15 Windows tests now prove:

1. A `Prepared` transaction cannot be exposed as last-known-good.
2. A `Healthy` transaction returns its exact target setup with all four signed payload hashes.
3. Tampering with the retained target setup prevents it from becoming a future rollback base.
4. A subsequent update can use the retained target package as its `previous` signed package.
5. A verified `Restored` transaction returns the previous setup as the current last-known-good package.
6. Snapshot rotation deletes the old snapshot only after the new snapshot contains both previous and target packages and the new DPAPI record points to it.

The full Windows integration run also passed the existing W22/W23/W60 audio/VPN/403 suite, W21 recovery tests, W24 native installer tests, W110 supervisor build/simulation, W114 single-installer packaging guard and W108 no-autoplay updater tests.

## Important remaining blockers

W115 is **rollback-cache groundwork**, not an enabled automatic updater.

- The main application still has no trusted Supervisor launch callsite.
- The production P-256 manifest key/public-key pin and Authenticode certificate fingerprint are not provisioned.
- No official production feed origin or atomic upload target is confirmed.
- The first signed bootstrap is still missing: before the first automatic update, the first production-signed installation needs a safe way to seed its own verified setup as the initial LKG package. `GetLastKnownGood` intentionally returns nothing until a transaction is `Healthy` or `Restored`.
- No real signed update, forced GUI crash, automatic rollback, owner-PC verification or final EXE+ZIP has been produced.

Do not populate pins with guessed values, do not use the Hostinger QA hostname as production, do not run the QA installer workflow as a release, and do not enable automatic installation until the real signed bootstrap and end-to-end rollback test pass.

## Next

Implement and test the first signed-install bootstrap, then wire the main app to the verified feed + durable journal + copied same-user Supervisor. Keep the existing one CELIKOM installer, AppId, install path and user session. Do not create a second product or release intermediate installers.
