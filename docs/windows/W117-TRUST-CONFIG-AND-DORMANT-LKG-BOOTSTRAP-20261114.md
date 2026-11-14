# W117 — shared fail-closed trust configuration and dormant LKG bootstrap

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
Product line: `main` only

## Source, backups and CI

- Exact code/test HEAD: `5b5a2e0845eb1d9f02400ae382d702c25abedf43`.
- Main CI [43587767442](https://github.com/manufact-test/nomusic/actions/runs/43587767442) — **SUCCESS**.
- Windows integration CI [43587767458](https://github.com/manufact-test/nomusic/actions/runs/43587767458) — **SUCCESS**.
- Pre-W117 trust/bootstrap backup: `backup/windows-main-pre-w117-trust-config-bootstrap-wire-20261114` @ `c058d00c4e5f20730552fe5ac3faaf10490279f3`.
- Pre-idle-gate backup: `backup/windows-main-pre-w117-playback-safe-bootstrap-gate-20261114` @ `e0fd39a449096d62b889b64c8d09ea8cb7659f73`.
- Pre-documentation backup: `backup/windows-main-pre-w117-docs-20261114` @ `5b5a2e0845eb1d9f02400ae382d702c25abedf43`.

## What changed

### One shared production trust tuple

Added `windows-companion/w15/Celikom.Companion/StableUpdateTrustConfiguration.cs`.

- Holds the official HTTPS origin, P-256 manifest public-key DER and Authenticode signer certificate SHA-256 fingerprint.
- The three production constants intentionally remain empty. No environment variable, command-line argument, registry entry, remote manifest or user-editable configuration can supply or override them.
- The manifest signing private key is never included in the client; it belongs only in protected release infrastructure.
- `TryCreate` rejects non-HTTPS URLs, non-root feed paths, URL user-info/query/fragment, malformed Base64/DER, non-P-256 curves and incomplete/non-hex signer fingerprints.
- The public-key byte array is defensively copied on construction and access.

### MainWindow startup bootstrap

- MainWindow starts `BootstrapStableRollbackIfConfiguredAsync` as a background task after normal startup.
- It exits immediately unless the complete production trust tuple is embedded.
- It also defers if the CELIKOM bridge is enabled or any Yandex Music process is running. No bootstrap download is started while Yandex playback may be active.
- When eventually configured, it calls `StableUpdateBootstrapper.EnsureInitialLastKnownGoodAsync` to verify an existing LKG or seed the first signed LKG package for the exact installed version.
- This method does not launch an installer, restart CELIKOM, change bridge state, reload Yandex or touch audio.
- Failure logs only the fixed code `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE`; no exception text, paths, feed URL, email, token or audio data is logged.

### Independent Supervisor

- `Celikom.UpdateSupervisor/Program.cs` now reads the same shared trust tuple.
- When production values remain empty or invalid, the helper exits code 3 before journal access, process supervision or installer execution.
- No CLI/environment/config fallback is accepted.

## Regression coverage

W15 tests cover:

1. Production trust remains disabled while the three production constants are empty.
2. A complete HTTPS/P-256/signer tuple is accepted.
3. P-384/non-P-256 keys are rejected.
4. HTTP, non-root feed paths and URL user-info are rejected.
5. Invalid Base64/DER and incomplete signer fingerprints are rejected.
6. Returned public-key bytes cannot be mutated by a caller.
7. Supervisor still exits code 3 while production trust is unprovisioned.
8. Static CI guard verifies MainWindow bootstrap is gated, waits for Yandex idle and contains no installer launch/restart call.

Both CI gates passed on the exact commit.

## What this does NOT enable

- Production P-256 public-key pin, Authenticode signer fingerprint and official HTTPS origin are still unprovisioned.
- No live signed feed/package publisher or atomic upload target exists.
- No signed `latest.json` consumer, update scheduler, user notice or install coordinator has been wired.
- The main app still has no trusted same-user Supervisor launch callsite.
- No real production-signed install, forced GUI crash, one-shot rollback or owner-PC account/audio test has run.
- No final EXE+ZIP was built or delivered.

The W117 startup hook is dormant by design until all production trust inputs are approved. Do not populate placeholders with guessed values. Do not use the Hostinger QA hostname as a production update feed. Do not paste private keys into chat or commit them.

## Next priority

Per W101 product policy, do not expand the updater further while the requested Windows audio fixes remain unfinished.

1. Fix the W98 Stage 5 isolated SQL restore assertion; the failed run [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358) completed private snapshot and original-audio hash restore checks but failed the isolated database invariant.
2. Investigate the current `.github/scripts/hostinger-stage5.sh` hardcoded Big City Life sidecar requirement before rerunning any production workflow. The sidecar staging job runs after this restore check, so the assertion may be checking future state too early.
3. Re-audit all active approved nonzero-gain replacements read-only, then use the W98 offline/private sidecar pipeline with exact source/version/gain/hash checks and rollback.
4. Keep #52, #53, #54, #57, #58 and VPN reconnect separate; CI is not owner acoustic acceptance.

Keep one existing CELIKOM Windows product and one `main` branch. No intermediate customer installer or mass release.
