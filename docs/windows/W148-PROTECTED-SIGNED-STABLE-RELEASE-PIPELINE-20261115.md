# W148 — CELIKOM Windows protected signed stable-release pipeline — 15 November 2026

> **SUPERSEDED FOR PRODUCT POLICY BY W150 (15 Nov 2026).** This file records an earlier implementation scaffold, not the final approved release design. Do not provision or purchase a commercial Authenticode certificate, do not use PFX credentials, and do not make Authenticode signer pins a prerequisite for CELIKOM's own updater. The owner has explicitly chosen to keep the existing Windows warning/“More info → Run anyway” installation experience and use CELIKOM's own P-256 signed-manifest trust plus SHA-256 package verification. The W148 workflow currently still contains the old PFX/Authenticode path and must be refactored in the final updater stage. The domain is already purchased; DNS/TLS and production publication wait until the planned infrastructure migration. See W150 and updated Issue #59.

## Exact status

- Working branch: `main` only. First W148 exact backup: `backup/windows-main-pre-w148-production-release-pipeline-20261115` @ `18ad2b8b6aa66012f5e2bb61d779d0e2dd51bd10`.
- Latest W148 code before this documentation update: `f70e1c23fe69be5ba3786d845b11459d1064bb5c`.
- **One existing CELIKOM Windows application**, no Windows TEST line. No signed installation, public stable feed or owner-PC automatic update performed yet. Owner has installed unsigned 0.24.37 with empty production trust pins; cannot auto-update without one trusted bootstrap.
- GitHub P0 infrastructure handoff: [issue #59](https://github.com/manufact-test/nomusic/issues/59). This is a concrete external owner/infra blocker; no one has been assigned to it automatically.

## Implementation performed

1. `.github/scripts/windows-stable-trust-embed.mjs` inserts only the actual vetted **public** P-256 SPKI key, official celikom.com HTTPS origin and trusted Authenticode certificate SHA-256 into `StableUpdateTrustConfiguration.cs` **in the release checkout**, not committed defaults. Source remains fail-closed empty on `main`; ordinary builds stay dormant. Refuses non-P256, staging origins, bad SHA and re-pinning.
2. `.github/scripts/windows-stable-keygen.mjs` generates an offline P-256 keypair on the release operator's trusted machine, writes 0600 private PEM + DER public key/base64, never prints the private key. **Do not run private key generation on untrusted/public runners or commit/upload the resulting private file.** Infra admin must place the PEM into protected GitHub secret without pasting it into chat.
3. `.github/scripts/windows-stable-release-verify.mjs` verifies detached DER signatures, exact immutable/latest JSON match, manifest schema 2, package SHA-256/size/version/sequence, four signed payload identities, and official CELIKOM host before deployment.
4. `.github/workflows/windows-stable-signed-release.yml` is manually dispatched **only from main**, requires `windows-stable-production` environment. It fails closed if version is not strictly newer than unsigned 0.24.37 or GUI/Supervisor/Inno versions are not already committed to `main`. It builds actual native assets, publishes current GUI + independent Supervisor from same source, checks the real issuer's code-signing EKU/Windows trust chain, exact DER fingerprint, signs all three EXEs using a protected genuine PFX + Authenticode timestamp, verifies signatures, uses the protected P-256 private key to sign immutable and latest manifests, verifies staged files, and hands them to publication job. **Not executed**, because legitimate release inputs are missing. HSM/cloud-only code-signing providers need provider-specific integration instead of this PFX route.
5. `.github/scripts/windows-stable-publish-hostinger.sh` publishes only after signed-release job: strict allowlist for official celikom.com origin and Hostinger document root, pinned SSH host/key fingerprint from existing QA flow, remote SHA256 check, monotonic sequence, immutable versioned EXE/manifest/signature, latest pair **last**, and rereads exact bytes from official HTTPS. Never touches the public QA/Test directory.
6. `.github/workflows/windows-w98-integration-ci.yml` checks manifest, pin embedding, prepared-release verification, offline-keygen tests and publisher shell syntax. No real certificate, SSH deployment or in-place owner-PC test occurs in CI.

## Provisioning required (GitHub admin / release operator, NOT ChatGPT connector)

Create protected GitHub Actions environment `windows-stable-production` with required reviewers and restrict to `main`. Configure **environment variables**:
- `CELIKOM_STABLE_ORIGIN`: actual approved working origin, e.g. `https://celikom.com` (must have DNS/TLS/Hostinger deployment target proven; do not assume registration makes it live).
- `CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64`: P-256 DER public key of the protected private signer.
- `CELIKOM_STABLE_SIGNER_SHA256`: SHA-256 hash of the trusted Authenticode certificate DER, not SHA-1 thumbprint.
- `CELIKOM_STABLE_DEPLOY_ROOT`: actual approved Hostinger root; publisher accepts only `/home/u235811320/domains/celikom.com/public_html` or `/home/u235811320/domains/updates.celikom.com/public_html`. If hosting differs, update and review allowlist before enabling release.

Configure **protected secrets**, NEVER paste into issue/chat/commit/log:
- `CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM`
- `CELIKOM_STABLE_PFX_BASE64` and `CELIKOM_STABLE_PFX_PASSWORD` for a *trusted public CA-issued code-signing certificate with exportable key*. Modern HSM/cloud certificates require separate supported signer implementation.
- `HOSTINGER_SSH_KEY` existing deployment SSH identity (confirm scoped to protected environment).

Before initial manual dispatch: update the ONE application `main` version consistently from 0.24.37 to at least 0.24.38 (GUI, Supervisor, Inno), with CI green. Provide a positive strictly increasing sequence and future UTC expiration up to 30 days. Do **not** publish unsigned W138 package. The first correctly signed version must be delivered once to owner as **trusted bootstrap** and installed over existing AppId preserving DPAPI/account/native files. The *next* signed higher release then tests fully automatic feed detect/download, safe point, Supervisor READY, installation, health/one-shot forced rollback on the real Windows PC. Only after owner's acceptance release to customers.

## Safety and unresolved work

- All new release/publisher steps are fail-closed and manually triggered. They are **code paths, not live credentials/certificates/deployment**.
- Existing full signed updater implementation is W101–W145. Actual production signature keys, Authenticode cert, official Hostinger DNS/TLS/root, protected secrets/environment, and owner bootstrap are not confirmed/provisioned by current connector permissions.
- No new EXE/ZIP produced; no public publication and no automatic delivery took place. GUI/audio/VPN and open issues #52 #53 #54 #56 #57 #58 remain for consolidated owner test. W119 and W139 are controlling.
