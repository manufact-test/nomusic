# W105–W108: signed stable updater trust chain and manual no-autoplay safety / 14 November 2026

## Exact source / backups / CI
- Canonical repo: `manufact-test/nomusic`, ONLY working branch `main`.
- Final W105–W108 verified code: `1ad2c63e78746db49ca8bca5e0c3c8bee2cbc48b`.
- Exact rollback: `backup/windows-main-post-w108-updater-guards-ci-green-20261114` @ same SHA.
- Pre-block safe source: `backup/windows-main-pre-w105-secure-package-staging-20261114` @ `553c5fb0059aa55e92959f93db1d18dbd2f9600e`.
- W105–W106 green checkpoint: `backup/windows-main-post-w105-w106-ci-green-pre-feed-20261114` @ `61dd35c07951be0b5f607afd2fbf548ff1509eeb`.
- W107 green checkpoint: `backup/windows-main-post-w107-signed-feed-ci-green-20261114` @ `685e95a2f40c0b58d06df4d907e856a8da13bc19`.
- Final main CI [43569385121](https://github.com/manufact-test/nomusic/actions/runs/43569385121) **SUCCESS**; full Windows CI [43569385123](https://github.com/manufact-test/nomusic/actions/runs/43569385123) **SUCCESS**. W107 CI [43568654764](https://github.com/manufact-test/nomusic/actions/runs/43568654764) / integration [43568654802](https://github.com/manufact-test/nomusic/actions/runs/43568654802) both SUCCESS.
- This whole change set touches **only Windows code, Windows tests and Windows integration CI** (and this documentation); no Yandex originals, extension, Android or private media.

## Implemented and tested

### W105: fail-closed staged signed EXE
`windows-companion/w15/Celikom.Companion/StableUpdatePackageStager.cs`
- Immutable versioned package via HTTPS, redirects disabled, anonymous/no-cookie/no-default-credential HTTP client.
- Bounded streaming transfer (125 MB cap, exact content length, byte count, streaming SHA256); interrupted, oversized, redirected or tampered file rejected with temp cleanup.
- Before treating staged EXE as trusted: re-read SHA256 and size, require WinVerifyTrust Authenticode, independently pinned SHA256 fingerprint of leaf signer certificate, CELIKOM PE company/product and exact file version. Recheck same trust before any future launch. No production certificate pin yet.
- `StableUpdateInstallSafety` rejects installation if bridge active, Yandex process present, playback unknown or another installer running.
- W15 tests cover valid hash download, unsigned fixture refusal, post-download tampering, truncation, redirects and playback gating.

### W106: targeted signed rollback directive (authorization only)
`StableUpdateManifestVerifier.cs`
- Ordinary stable releases must increase version and monotonically increase release sequence.
- Only separately signed `rollback: {fromVersion,toVersion}` with mandatory flag, a newer release sequence, exact `fromVersion` equal to the running bad release and strictly lower `toVersion` is accepted. Remote signed rollback must still pass exact HTTPS immutable package path, expiry, pin, version and SHA checks.
- Explicitly rejects replay, wrong source, optional rollback and unsigned/arbitrary downgrade.
- This does **not** restore or install anything by itself.

### W107: signed feed discovery (read-only, not wired to users)
`StableUpdateManifestFetcher.cs`
- Strict official HTTPS root; fetches `/CELIKOM/Windows/Updates/stable/latest.json` and `latest.json.sig` independently with no redirects, no cookies, short timeout and 16 KB/80 B caps; checks detached NIST P-256 signature using a caller-supplied **pinned** public key and all `StableUpdateManifestVerifier` constraints.
- Test fixture generates transient ECDSA key only in memory; no production signing key generated or stored, no production feed fetch wired yet.

### W108: manual update protects music and honest health reporting
`AppUpdateManager.cs`, `MainWindow.cs`, `.github/workflows/windows-w98-integration-ci.yml`
- Existing staff-only local updater refuses installation if Yandex process runs, if the CELIKOM bridge is enabled or if process-state inspection fails; tells user to finish playback and stop CELIKOM.
- Pending ticket is cleared on refused launch, but NOT when installer was already successfully launched.
- Post-install no longer automatically launches Yandex or claims `APP_UPDATE_COMPLETED` just because `--complete-update` launched. It logs new EXE startup and actual bridge/native module status separately.
- Windows integration CI statically rejects regression that autolaunches Yandex from post-update completion or reinstates false `APP_UPDATE_COMPLETED`.

## Release blockers (KEEP OPEN)
1. Cryptographically legitimate CELIKOM Authenticode code-signing certificate and separate release-signing key with its **public key pinned into the built app**. Do not invent or request a new user email/secret, do not use self-signed/test keys in production.
2. Actual published signed stable feed + immutable signed installer on confirmed official HTTPS origin. Current W107 is a verifier, not a scheduled consumer check.
3. Customer-facing background stable check (startup, every ~6 hours), bounded retries/download, nonblocking notice, safe/idle installation scheduling.
4. An **independent supervised** install transaction: cached last-known-good signed package, process/DPAPI/bridge health proof, timeout/crash rollback from exact verified previous package, no loops, signed monotonic remote rollback enforcement. W106 is only the rollback authorization contract.
5. Exact AppId/in-place preservation, signature and failure/restore end-to-end Windows CI, then **one** integrated next release EXE+ZIP for owner acceptance. No partial or mass release.
6. Actual owner-PC acceptance for VPN reconnection, #52/#53/#54/#56/#57/#58 and startup/reboot/diagnostics. CI cannot prove audible replacements, stable volume or absence of hiss.

## Rules
Continue ONLY on `main` with exact `backup/*` prior to substantial edits. Do not touch Android, browser extension, original Yandex assets, private audio or unrelated servers. No user-facing intermediate installer, no mass rollout until owner signs off. Treat green CI as code proof, not field-acoustic proof.
