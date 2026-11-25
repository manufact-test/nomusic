# CELIKOM A1 — FlokiNET delivery repair (2026-11-25)

## Contract, not negotiable
GitHub is private source/build infrastructure. Owners and future customers download apps only from \`celikom.com\`, never from a GitHub draft release. Keep A1 independent of the Windows branch and preserve the existing APK signature, package ID, audio guards, and the read-only CI/production boundary.

## Verified starting point
- Android A1 BETA16 owner APK is already signed in private draft \`celikom-a1-owner-45652314715-1\`, source run \`45652314715\` succeeded. Name \`CELIKOM-A1-RAMIL-AU-BETA16-HONOR50-20261125.apk\`, size \`71585772\`, SHA-256 \`5faf46740dce159aee6a04bee3020aba046f1ae7c61bf9e53e649d4fc4bb3035\`.
- A1 BETA15 was successfully distributed on 25 November via the **existing** \`celikom.com/downloads/a1/<48-hex-token>/...\` capability route; independent HTTPS 200, signer, file size and SHA-256 were validated by \`45644488030\`. Thus Nginx and the restricted \`/usr/local/sbin/celikom-a1-apk-receive\` are proven, but **BETA16 has not been published there yet**.
- Existing hosted workflow \`.github/workflows/android-a1-owner-floki-download.yml\` uses \`ubuntu-latest\`, can directly invoke restricted SSH as \`celikom-deploy\`, and worked for BETA15. Later jobs failed before startup; there is no proof this runner currently works.
- The sole self-hosted CI runner \`celikom-ci-smoke-only\` is **deliberately denied host SSH**, including public host port 22 and Docker bridge gateway. NEVER open host SSH/Docker socket or mount production paths just to ship APKs.

## Durable Floki-side staged route (new code)
1. Trusted \`main\` workflow \`.github/workflows/android-a1-owner-floki-spool.yml\` checks successful exact ARM13 run and trusted private draft, recomputes all source/digest checks, independently verifies signing certificate and package name, then stages *data only* with \`.github/scripts/floki-a1-signed-spool.py\` inside the isolated runner.
2. Runner's private directory \`/home/runner/celikom-a1-signed-spool\` is host-mounted at \`/srv/celikom/ci-runner/runner/celikom-a1-signed-spool\`. No CI network permission to access Nginx, API, SSH or root.
3. Trusted root-owned \`.github/scripts/floki-a1-root-signed-spool-consumer.py\` checks file descriptors against symlink/race attacks; validates source metadata, original APK signer SHA-256 \`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf\`, exact package \`pro.celikom.yandex.nativeclonelab\`, size and SHA. It calls the **already installed unprivileged** \`celikom-a1-apk-receive\` and verifies actual HTTPS response size+SHA before writing a trusted receipt.
4. Systemd \`celikom-a1-signed-owner.timer\` checks the spool roughly every minute. This **requires one-time root installation**; it cannot be installed from the isolated runner (security feature).
5. Consumers get only the final URL from \`celikom.com\`. A capability-based owner beta link is NOT a finished public customer updater; auth and release channels for customers remain separate acceptance work.

## One-time host activation — only after trusted review and stage success
The pinned installation source is \`.github/scripts/floki-a1-signed-spool-bootstrap.sh\` at commit \`3aa040c29e505f137953fe7fb113c49b27e63886\`, Git blob \`46ee3af7012a536ce11101685e3edb76aa5731fb\`. It independently reads the root consumer from private read-only mirror commit \`f5c963cb8828f84ba2c526c8e07460d8a36b58ec\`, Git blob \`a00a77580a413c9cf9babb57efb0225b244d6757\`, and refuses mismatches.

For a separately authorized trusted FlokiNET root maintenance session, **not a GitHub CI job**, the operator can execute the following one-time step. Do NOT publish BETA16 without verified source staging.

\`\`\`bash
sudo bash <<'BASH'
set -Eeuo pipefail
umask 077
systemctl start celikom-mirror-sync.service
d=$(mktemp -d /root/celikom-a1-activation.XXXXXXXX)
trap 'rm -rf -- "$d"' EXIT
runuser -u celikom-mirror -- git --git-dir=/home/celikom-mirror/github-mirror.git show \
  3aa040c29e505f137953fe7fb113c49b27e63886:.github/scripts/floki-a1-signed-spool-bootstrap.sh > "$d/bootstrap.sh"
test "$(git hash-object "$d/bootstrap.sh")" = 46ee3af7012a536ce11101685e3edb76aa5731fb
bash -n "$d/bootstrap.sh"
bash "$d/bootstrap.sh"
BASH
\`\`\`

The installer is intentionally fail-closed, does not change Nginx/API/Windows, uses Ubuntu 24.04's \`apksigner\` and \`aapt\` packages for signer verification, and installs only a root-owned data-only consumer/timer.

## Acceptance — no more GitHub links to owner
- Self-hosted stage job reports \`A1_SIGNED_SPOOL_READY\` for exactly run \`45652314715\`, attempt 1, expected SHA.
- Trusted consumer reports \`A1_ROOT_SIGNER_AND_PACKAGE_VERIFIED\`, \`A1_ROOT_EXTERNAL_HTTPS_200_SIZE_SHA256_VERIFIED\`, \`A1_ROOT_OWNER_DOWNLOAD_READY\`.
- Read \`/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-45652314715-1.json\` and extract the *actual* \`url\`.
- Validate an independent HTTPS GET HTTP 200 with exact size \`71585772\` and SHA \`5faf46740dce159aee6a04bee3020aba046f1ae7c61bf9e53e649d4fc4bb3035\`. Only then give the owner the direct link and request the one-phone Ramil «Ау» / diagnostic TXT check.
- Until those checks pass, distribution remains **NOT COMPLETE**. No fabricated FlokiNET URLs, no public GitHub release, no claim that audio replacement works.

## Previous failed approach not to repeat
Do not assign \`FLOKI_DEPLOY_CONNECTION\` or SSH operations to \`celikom-ci-smoke-only\`. The isolated runner is explicitly denied host port 22 and the Docker gateway; those refusals are **expected security**, not a broken SSH key. Do not weaken isolation to fix delivery. The independent root promotion is the permanent solution.

## Latest checkpoint — signed BETA16 already staged on Floki runner

On 25 November, workflow run **45663779624** completed **success** on **celikom-floki-ci01**, label \`celikom-ci-smoke-only\`. Observed actual log:

\`\`\`text
Ran 6 tests in 0.147s
OK
A1_SOURCE_RUN_AND_BOTH_NATIVE_JVM_GATES_VERIFIED
A1_PRIVATE_RELEASE_PROVENANCE_SIZE_AND_DIGEST_VERIFIED
A1_APKSIGNER_AND_ORIGINAL_PACKAGE_VERIFIED
A1_SIGNED_SPOOL_READY 45652314715 1 5faf46740dce159aee6a04bee3020aba046f1ae7c61bf9e53e649d4fc4bb3035 root-promotion-pending
A1_APK_PRIVATELY_STAGED_AWAIT_INDEPENDENT_ROOT_PROMOTION
\`\`\`

**APK build and runner staging are complete. Stop rebuilding/retrying and do not switch runner just to stage the same file again.** Additional CI runner may serve other tasks, but it cannot (and must not) bypass the host isolation for root publication.

**Only remaining delivery blocker:** the one-time trusted root bootstrap described above must be executed on the FlokiNET host. Then read its trusted receipt and independently verify HTTPS 200/size/SHA-256 before giving the owner a URL. Installing the root consumer on CI is prohibited. These commands do not require the owner to run ADB, Android IDE, or a second phone.


## Root activation failed once — narrow Ubuntu verifier fix (25 November)

Owner ran the original verified bootstrap. Ubuntu installed `apksigner` and `aapt`, and created/enabled `celikom-a1-signed-owner.timer`. The initial `celikom-a1-signed-owner.service` failed at consumer line 215 with `A1_ROOT_MISSING_SIGNING_VERIFIER` **before** inspecting or publishing any APK. Original consumer rejected any symbolic link even when Ubuntu packages provided a trusted, root-owned binary through one. The failure is limited to verifier path admission; it is not an Android build failure.

Patched the root consumer at commit `7366d6bd7b6fdddcea3ae27b2cf0658473dda4b3`, Git blob `a9e915186e7c0e3bbce0b8ffda7c046500ca99a3`: resolve strict path, ensure executable under distro-controlled `/usr` outside `/usr/local`, ensure both requested path and resolved target and their parents are root-owned and not group/world-writable. Certificate and exact application ID verification are unchanged. Updated fresh-install bootstrap source pin.

Trusted **one-time repair script** `.github/scripts/floki-a1-signed-verifier-ubuntu-recovery.sh` was added at commit `fc240ecce39ec0d268b3cb6b992392438cce5d49`, Git blob `db02468bf5ef5d2a78259e6387d26ffff75d6882`. An operator with root authority may retrieve it from the read-only mirror and verify that exact blob before execution. The script refuses unexpected installed consumer state, stops only the A1 timer/service during atomic replacement, and resumes the timer. It starts the pre-existing service and prints trusted BETA16 receipt if successful. Do **not** run first-time bootstrap again or restage BETA16.

This repair is committed, **but not verified on the live server yet**. Do not report release complete until trusted root receipt and independent external HTTPS file hash are verified.

## Corrected Ubuntu verifier symlink mode (same date)

First surgical repair installed consumer blob `a9e915186e7c0e3bbce0b8ffda7c046500ca99a3` successfully, but the service then failed with `A1_ROOT_UNTRUSTED_SIGNING_VERIFIER_PATH` from the group/world-writable bit check of a POSIX symbolic link. Root-owned Ubuntu symlinks normally have `0777` which is not their effective write permission. Confirmed against local real root-owned `/bin -> /usr/bin` chain; root-owned regular `0777` executables and writable directories remain rejected.

Corrected trusted consumer at commit `b7764101e878ea7c6117dfca6286ca0f20888f26`, blob `abde17a59570260cb590a4873408577acfa1b56c`: accept 0777 **only for root-owned symlinks** while retaining root-owned non-group/world-writable real files/directories, executable check, resolved final target confined under `/usr` (not `/usr/local`), and pinned signature checks.

Updated recovery script at commit `f2bb9a516eda27de9af181fffcb5ae9021e64abd`, blob `d12d4038a71e9d16bd380ec1b78e5649f242266e`, to accept the previous failed installed consumers but install only corrected code. Future first-time installer pins also updated. This corrected repair has **not yet been run or validated on Floki**; do not claim public BETA16 live.
