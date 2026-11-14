# W113 — CELIKOM Windows schema-2 stable manifest generation / 14 November 2026

## Source and CI
- Repository: manufact-test/nomusic; only active working branch: main.
- Implementation commit: c7451d90863581794c70df7a3dc8c2525ee4930c.
- Exact pre-W113 backup: backup/windows-main-pre-w113-stable-manifest-publisher-20261114 @ d136d52d595574c25461fc05590ac7078a739cf6.
- Main CI [43578863477](https://github.com/manufact-test/nomusic/actions/runs/43578863477) SUCCESS.
- Windows integration [43578863492](https://github.com/manufact-test/nomusic/actions/runs/43578863492) SUCCESS.

## What W113 adds
- .github/scripts/windows-stable-manifest.mjs builds the exact schema-2 JSON consumed by StableUpdateManifestVerifier. W116 also writes an immutable version-addressed copy at `{version}/manifest.json` with its detached signature at `{version}/manifest.json.sig`, alongside the mutable `latest.json` pair.
- Hashes the exact installer package and the installed CELIKOM executable, native host and renderer. W114 subsequently adds the Supervisor as the fourth payload.
- Requires a P-256 private key and an independently pinned SPKI public-key DER; refuses to sign if the derived public key differs from the client pin.
- Signs the exact UTF-8 JSON bytes with SHA-256 / ECDSA P-256 and DER sequence encoding.
- Validates version, a positive sequence input (the release pipeline must supply a monotonic value), HTTPS root shape, immutable versioned package path, UTC publication/expiry and bounded lifetime.
- Tests use a generated throwaway P-256 key only. No test key is a production trust anchor.

## What W113 does NOT do
- It is a manifest generator, not a live publisher. No feed has been deployed and no stable manifest/package was uploaded. The versioned manifest/signature are generated locally; the package remains a separate artifact that must be uploaded to the exact version path in the manifest.
- Production private key/public-key pin and Authenticode certificate fingerprint are not provisioned. The application still has no production pin.
- The Hostinger private QA hostname used in test fixtures is not automatically the official stable-feed origin. Confirm the production HTTPS origin and upload destination from approved deployment configuration before publishing.
- No automatic update, installer launch, supervisor launch, real crash recovery or owner-PC test is enabled.

## W116 follow-on
The immutable versioned manifest/signature are now consumed by `StableUpdateBootstrapper` to seed the first LKG package for the exact currently installed signed build. The bootstrap code is not wired to the main app yet. Provision production signing pins, confirm the official feed origin and upload target, then wire bootstrap and the normal signed update flow. Do not publish from the Hostinger QA hostname or enable automatic installation before real end-to-end rollback verification.

## W117 follow-on

The first-LKG bootstrap is now wired to MainWindow startup through the shared `StableUpdateTrustConfiguration`, but the origin, P-256 public key and Authenticode signer fingerprint remain intentionally empty. Startup skips the operation unless the complete trust tuple exists and CELIKOM/Yandex are idle. The Supervisor consumes the same shared trust source and remains fail-closed. This is only bootstrap wiring; no live feed, latest-manifest consumer, trusted Supervisor launch or automatic installer is enabled. Current Windows priority returns to owner-requested audio fixes before full updater expansion.
