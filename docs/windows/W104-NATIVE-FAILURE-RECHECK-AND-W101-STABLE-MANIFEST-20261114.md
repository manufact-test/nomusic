# W104 native failure compatibility + W101 signed manifest contract — 14 Nov 2026

## Source / exact rollback
- Repository: `manufact-test/nomusic`, **single active branch `main`**.
- Last code commit here: `4722731378170fb7c6a761a0b0ec716c0fe0e7b8`.
- Pre-W104 complete original rollback: `backup/windows-main-pre-native-failure-recheck-20261114` @ `f82dbe4448ff743945da4d4d26f159bfbaeb2766`.
- First W104 CI-green exact backup: `backup/windows-main-post-native-failure-recheck-ci-green-20261114` @ `f4449475ff0298c82b52426ded28b73217ec2439`.
- W101 verifier baseline: `backup/windows-main-pre-w101-signed-feed-contract-20261114` @ `3cc58b93a244d3711b7cda06010e550212731935`.
- Latest full Windows W104 source `3cc58b93`: main CI [43528538262](https://github.com/manufact-test/nomusic/actions/runs/43528538262) SUCCESS; Windows integration [43528538351](https://github.com/manufact-test/nomusic/actions/runs/43528538351) SUCCESS. **Check newer `47227313` CI before claiming W101 verified.**

## W104 implemented
- `windows-companion/w15/Celikom.Companion/MainWindow.cs`: native HOST_ERROR heartbeat, missing native startup handshake after 22 seconds, and failed native module install/upgrade trigger read-only `OfficialYandexCatalog.RefreshAsync(force:true)` and subsequent local identity re-inspection.
- `YandexFailureRecheckGate.cs`: synchronized/coalesced trigger with 2/4/8/15-minute backoff; successful native handshake resets backoff. AUDIO source failures/403 and ORIGINAL track events do not trigger a false vendor failure.
- Tests in `Celikom.Companion.Tests/Program.cs` cover statuses, overlapping triggers, bounded backoff and recovery.
- No change to DSP, original media, signed URL, entitlement, native patch automation or Yandex installer.

## W101 groundwork only, NOT a production updater
- `StableUpdateManifestVerifier.cs` verifies detached NIST P-256/SHA256 release-manifest signatures against a caller-supplied pinned public key; validates immutable stable origin/version, new version and monotonic sequence, signed publisher claim, package byte size/hash and bounded expiration. Test fixture generates its own signing key solely in-memory.
- No official production signing key/pinned key has been integrated and there is no Authenticode-signed CELIKOM installer. Do not derive a key from the unsigned manifest, download unsigned code, trust the SHA in unsigned JSON, or permit unattended installation.
- No background stable-feed check/download, playback-idle install scheduler, independent post-upgrade health/rollback supervisor or signed rollback directive has been implemented.
- `AppUpdateManager` remains staff-only local/manual and accepts unsigned internal packages with a warning. Stable auto-install is disabled by the absence of an entry point; do not enable it prematurely.

## Acceptance and remaining obligations
- Existing #52/#53/#54/#56/#57/#58 and VPN issues still require actual playback and performance QA on owner's Windows PC; CI alone cannot certify acoustic quality.
- Complete W101 cryptographically signed distribution, fail-safe independent rollback, no-audio-interruption and end-to-end Windows signature tests before any mass rollout. Do not ask user for credentials or create new experimental branches; reuse approved repository/deployment setup.
- Then one integrated EXE+ZIP from the same AppId/install directory, exact-commit CI and owner in-place upgrade/restore QA. **No installer or mass release was produced in W104/W101 guard work.**
