# W197 — Windows OTA self-verification size-limit fix and 0.24.64 candidate (28 November 2026)

## Root cause

The installed 0.24.62 and published 0.24.63 packages were valid: their signed manifests, package SHA-256 values, and PE versions verified. The actual installed Companion and UpdateSupervisor executable hashes also matched the signed manifest.

The failure was the local verifier's default size ceiling:

- Companion executable: **144,412,407 bytes**.
- UpdateSupervisor executable: **144,445,634 bytes**.
- `StableUpdatePayloadVerifier.MatchesFile` and `OpenVerifiedReadHandle` defaulted to **125,000,000 bytes**.
- Both executables were therefore rejected despite matching SHA-256. Native host and renderer passed.

This blocked current-install verification and supervisor launch before OTA could proceed. The same defect existed in both 0.24.62 and 0.24.63.

## Fix merged to main

- PR [#75](https://github.com/manufact-test/nomusic/pull/75) merged as `3e5f8ae72d51123dec05e5c5e9196535c9b235c1`.
- Installed-payload and verified-executable defaults raised to **250,000,000 bytes**.
- The signed installer download/package ceiling remains **125,000,000 bytes**.
- Restored the existing local staging filename `CELIKOM-W15-WINDOWS-UNSIGNED`. The protected signed-release workflow continues to override the production output name with `/F CELIKOM-Windows-<version>`; production naming is unchanged.

## Validation

- Generic CI: [46139959353](https://github.com/manufact-test/nomusic/actions/runs/46139959353) — SUCCESS.
- Windows integration CI: [46139959369](https://github.com/manufact-test/nomusic/actions/runs/46139959369) — SUCCESS.
- Live Windows OTA matrix: [46139959359](https://github.com/manufact-test/nomusic/actions/runs/46139959359) — SUCCESS for both public 0.24.62 and 0.24.63.
- Both releases passed all four installed payload hashes, the default `MatchesFile` verifier, the default supervisor launch handle, and fresh LKG bootstrap. The synthetic stale-LKG rejection invariant also passed.
- No owner-device journal was read or inferred. No diagnostics need to be repeated.

## 0.24.64 candidate

Main was bumped to app/Supervisor **0.24.64.0**, stable release **0.24.64**, sequence **11**. The existing owner-build trigger ran:

- Build: [46140222345](https://github.com/manufact-test/nomusic/actions/runs/46140222345) — SUCCESS.
- P-256 public-key fingerprint: `46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95`.
- Signed manifest and release verification: SUCCESS.
- Package SHA-256: `59f4ea6424041f7aaa6cd88d429a3060fa8340fdd7932ef84de186bdb26c56ef`.
- Stable candidate artifact ID: `15260863373`, SHA-256 `9f1404c6c8a1af0ed86c5b1c3c152d7334bfdd0257591e6c5a34913941d60645`.
- Floki transfer artifact ID: `15261072843`, SHA-256 `0b86069179dbfee01150bf3c01485ea8bcefadb9cfccd57658c4c538ad80af4d`.
- Manifest expiry: **2026-12-05 11:31:05 UTC**. Action artifacts expire **2026-11-29 11:32 UTC**.

The candidate build's production Hostinger and Floki publish jobs were **SKIPPED**. Public `latest.json`, the immutable 0.24.63 manifest and package remain unchanged at sequence 10. **0.24.64 is not published yet.**

## Protected publication workflow repair (28 November 2026)

The first manual 0.24.64 promotion attempt, [Actions 46141150754](https://github.com/manufact-test/nomusic/actions/runs/46141150754), failed closed in `prepare` before signing or publication because repository variable `CELIKOM_STABLE_PUBLISHER` was empty. No protected production approval, server mutation, or public feed change occurred.

The target was then resolved from the actual release path, not guessed:
- W194 promoted 0.24.63 through the existing Floki signed spool and updated `.github/release/windows-customer-stable.json`.
- W195 confirms the public customer feed is served from Floki's `/srv/celikom-releases/public/windows-customer-stable`.
- The Floki customer consumer reads the explicit `windows-customer-stable.json` approval record; staging to the local Floki stable feed alone does not publish the customer feed.

PR [#76](https://github.com/manufact-test/nomusic/pull/76) merged as `c1f59b7fd5789e0a828f5a48ce0b118a2bb6ceba`:
- Manual workflow now has `publish_target`, default **floki**; the unset repository variable is no longer a blocker.
- After the existing `windows-stable-production` approval and signed-spool stage, the Floki job verifies the recorded approval, pinned P-256 key, signed manifest, sequence/version and installer SHA-256, then updates the explicit customer approval record with `owner_accepted=true`.
- The customer approval update is monotonic and idempotent.
- A post-promotion job waits for the customer timer and verifies exact public latest bytes, immutable manifest/signature and full installer SHA-256 at both public installer URLs.

PR CI: generic [46142163668](https://github.com/manufact-test/nomusic/actions/runs/46142163668) and Windows integration [46142163775](https://github.com/manufact-test/nomusic/actions/runs/46142163775) — SUCCESS. Post-merge main generic CI [46142412039](https://github.com/manufact-test/nomusic/actions/runs/46142412039) and Windows integration [46142412032](https://github.com/manufact-test/nomusic/actions/runs/46142412032) — SUCCESS. Publisher static gates [46142412042](https://github.com/manufact-test/nomusic/actions/runs/46142412042) remain in progress without starting a job step; the new workflow contract test already passed in PR generic CI and Windows integration CI.

Current public approval record remains **0.24.63 / sequence 10**. The previous owner candidate artifact from run 46140222345 is not used by the corrected flow; the next manual run rebuilds the exact signed package from current main. **0.24.64 remains unpublished until that run passes its protected gate and public HTTPS verification.**

## Next actions — preserve the existing gates

1. Open [the signed stable release workflow](https://github.com/manufact-test/nomusic/actions/workflows/windows-stable-signed-release.yml), run it with version `0.24.64`, sequence `11`, and `publish_to_production=true`. Complete the existing `windows-stable-production` environment approval. Do not bypass the gate.
2. After publication, independently verify public latest, signature, immutable versioned manifest, installer URL and package SHA-256. Do not infer publication from the candidate artifact.
3. The installed 0.24.62 and public 0.24.63 binaries still contain the old 125 MB limit; neither can self-update to the fix. A **one-time 0.24.64 bootstrap installation is technically unavoidable**. Do not send a manual installer or ask the owner to install it until the owner explicitly consents.
4. After that one-time bootstrap, verify normal OTA: quiet background download while Yandex plays, verified package persisted after close, automatic installation at the next ordinary CELIKOM launch, and no Stop/forced playback interruption.

## Boundaries

No Android, browser extension, Windows audio engine, customer audio data, or new update channel was changed. Do not repeat W196 diagnostics or ask for the same owner test. Keep the existing single Windows stable feed and protected GitHub publication mechanism.
