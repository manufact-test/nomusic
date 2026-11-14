# W123 — Signed no-update result for stable manifest polling — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W123 code backup: `backup/windows-main-pre-w123-manifest-no-update-20261114` @ `40b8898c6c2489313f80b0e7a979b9e793e47dac`.
- W123 implementation commit: `5ae6b285889ca542d2ba30bbe25b5d3233800333`.
- Exact green rollback snapshot: `backup/windows-main-post-w123-ci-green-20261114` @ the W123 commit.
- Main CI [43598711117](https://github.com/manufact-test/nomusic/actions/runs/43598711117) and Windows integration CI [43598711096](https://github.com/manufact-test/nomusic/actions/runs/43598711096) — **SUCCESS**.

## Changes

- Added `StableUpdateManifestVerifier.VerifyIfNewer` and `StableUpdateManifestFetcher.FetchSignedIfNewerAsync`.
- The detached signature is always verified before a same-sequence manifest can be reported as a normal no-update result.
- An equal authenticated sequence returns `null` (no update); an older sequence or invalid signature remains a hard rejection.
- Existing strict `Verify` and bootstrap/version-specific fetch behavior remain unchanged.
- Tests cover equal-sequence no-update, tampered signature rejection, older-sequence rejection and the signed feed transport seam.

This is required for a real periodic stable updater: a current manifest must not be misclassified as a broken feed. It does not fetch from a production origin, launch an installer or activate the Supervisor. Production trust values remain empty. No installer was built.

