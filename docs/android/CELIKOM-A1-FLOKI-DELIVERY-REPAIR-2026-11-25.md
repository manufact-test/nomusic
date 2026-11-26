# CURRENT HANDOFF — 27 November 2026 (BETA23 signed Floki delivery verified)

- Native source `d598c0fc043aa4fedf5a27223b4797af474b8955`, run `45903557070` (attempt 1) **SUCCESS**, separate JVM `45903454018` and clone differential `45903409452` both **SUCCESS**. APK `CELIKOM-A1-RAMIL-AU-BETA23-HONOR50-20261127.apk` size `71593964`, sha256 `5b008cc092b1b24ad6b916efb474b096e8b1a4fc5a370ace1f24adaff747b439`, unpublished draft release `459959795`.
- Main request `.github/deploy/a1-owner-download-request.json` contains run ID `45903557070`, attempt `1`, release `459959795`. Trusted-main Floki spool `45904921524` **SUCCESS**, exact original app signer/package verified, root receipt verified, actual HTTPS digest and size verified, owner URL committed to unpublished draft/read back. **Capability URL only sent privately to owner**, never in public source/docs/Actions summaries.
- CI runner `celikom-floki-ci02` assigned original delivery `45904842417` and stuck before any job step. Attempted exact cancel/force-cancel via one-time narrow hosted action `45905031509` **SUCCESS** (cancellation requested; stuck runner may take time to settle). Recovery used a separate concurrency group and healthy `celikom-floki-ci01` for success. Do not let a stale CI02 job block subsequent deliveries; restore the normal group only after previous job is actually canceled or runner repaired. No CI root/SSH/network permission changes.
- This build changes owner-only signed original FileInfoApi codec negotiation `codecs=mp3` for exactly the Ramil trial, to test AAC original decoder vs alternate MPEG mismatch identified in BETA22 private phone diagnostics. No acoustic confirmation yet; stable Android, Windows, API, Nginx, signer and root consumer unchanged.

---

# CURRENT HANDOFF — 27 November 2026 (BETA22 owner delivery confirmed)

- Source commit `a535cbf3de21faaff7aa32ea6fb3c75a93459b70` experimental Android; signed native/export workflow run `45899350738` attempt 1 **SUCCESS**; separate clone differential run `45899350523` **SUCCESS**. APK `CELIKOM-A1-RAMIL-AU-BETA22-HONOR50-20261127.apk` size `71593964`, SHA256 `836be0f0ed2006455cd6c4e20f3f0a2a45a82455626d1eb530e250c25eeca7de`, unpublished owner draft release `459934139`.
- Data-only main request `.github/deploy/a1-owner-download-request.json` targets source run `45899350738`, attempt `1`, release `459934139`. Trusted main Floki signed spool run `45901657011` **SUCCESS** on `celikom-floki-ci01`: independently reverified signer, package, SHA, size, root receipt, actual HTTPS and unpublished draft owner-link readback. Capability URL shared **only privately with owner**, never in Git, Actions logs or docs.
- First delivery run `45900744210` remained stuck on `celikom-floki-ci02` before job steps. Retried same request, issued narrowly scoped cancel/force-cancel request for that stuck run, then used a separate recovery concurrency group on healthy runner `celikom-floki-ci01`. **After successful delivery, restored original main workflow concurrency group and deleted one-time cancellation workflow.** Do not widen host SSH, Docker, root or CI privileges.
- BETA22 is a **read-only runtime period-to-renderer SampleStream identity experiment**, not verified audible replacement. Owner testing on real Honor 50 is still required. Stable Android/Windows/API/Nginx/signature/root consumer untouched. Historical BETA21 delivery remains below.

---

# CURRENT HANDOFF — 26 November 2026 (BETA21 FlokiNET delivery confirmed)

## Exact accepted owner APK and delivery evidence

- Android A1 BETA21 source commit `4b3e966aeab71d90b307110a72f222fefde46fdd` on `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Native signed build/export run `45863084301`, attempt 1, all JVM + Android13 jobs **success**. Separate clone differential `45863084416` **success**.
- Exact APK: `CELIKOM-A1-RAMIL-AU-BETA21-HONOR50-20261126.apk`, 71593964 bytes, SHA-256 `80f4b0056107486ae43bb656e9331d6b7b96d21493f9e0aba7ceb171ece2db91`. Source unpublished owner draft release ID `459698802` (must stay unpublished).
- Main data-only request `.github/deploy/a1-owner-download-request.json`: run ID `45863084301`, attempt `1`, release ID `459698802`. Floki isolated runner/stage + independent root consumer and HTTPS verified receipt through `.github/workflows/android-a1-owner-floki-spool.yml`, delivery run `45865042744` **SUCCESS**. Root receipt + unpublished draft owner URL readback matched. Owner received celikom.com link in the chat only; **never publish capability URL, private TXT, tokens or root receipts in public GitHub**.
- Stable Android, Windows, backend, Nginx, receiver, independent root consumer and signer were unchanged. Legacy `android-a1-owner-floki-download.yml` remains disabled.

## Why BETA21 and what remains

- Honor 50 BETA20 confirmed server grant, exact first-open arm, alternate audio `OPEN/READ`, but **user did not hear alternate**. Audio renderer `STATE_NOT2=MANY`, `STATE2=NONE`, `READ_RETURN_MINUS3=MANY`, no active non-EOS audio evidence. Encoded byte read is not audible proof. Private diagnostic `CELIKOM-A1-Diagnostics-1795710702903.txt` stays in chat only.
- BETA20 still had a second premature arming call in dynamically discovered factory product construction. Fix `7fe6dcdd8fa98252eaff19dab9a3156b4b1ab645` leaves deferred alternate arming exclusively at genuine original Exo first `open()`. Proven JVM, native and clone gates; not yet acoustic.
- New passively observed Android framework output: `MediaCodec.configure` audio MIME MPEG/AAC/other, `MediaCodec.start`, `AudioTrack.play` counters. No audio mutation or second player. Evidence may distinguish decode/output activity, cannot prove active selected Exo path by itself.
- Isolated private signed-2025 XAPK process topology run `45862436035` finds no explicitly media-named secondary playback service (3 media-named all main, 2 separate non-media services), so no evidenced reason to migrate hook to other process. Not a complete runtime process proof.
- **NEXT:** owner installs BETA21 over BETA20 (retain data), plays Ramil' «Ау» publisher `144530503`, album `38902809`, listens 00:43–00:54 and exports TXT. Check `A1_TRACKID_BETA21_ACTUAL_OPEN_ONLY_CODEC_OUTPUT_WITNESS_20261126`, signed first-open, alt reads, codec/output and renderer. `acoustic_replacement_proven=false` until owner confirms actual sound. No new delivery without evidence-backed root-cause fix.

## Historical records below

---

# CURRENT HANDOFF — 26 November 2026 (BETA20 delivered, awaiting acoustic acceptance)

## Verified owner delivery

- Owner-only Android A1 BETA20 built from source commit `661d5a428e0ed90c3744affefd799d6443af5fe0` on `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; source workflow `45854781668`, attempt `1`, JVM/native ARM13 jobs **success**. APK `CELIKOM-A1-RAMIL-AU-BETA20-HONOR50-20261126.apk`, `71593964` bytes, SHA-256 `313bac3833177a25fa164277537d3520a36a2f371293e3af549df518b683fc89`.
- Source unpublished owner draft release `459645155` contains APK, SHA256SUMS, build provenance and README. It is not a public customer release. **Never copy the owner capability URL to Git, public Actions logs/summaries, docs, screenshots, or commits.** Owner received the Floki URL directly in chat.
- Trusted-main **data-only** Floki spool workflow `.github/workflows/android-a1-owner-floki-spool.yml` run `45857047886`, job `140038049838`, **success**: validated source run, original APK certificate/package, source provenance and size/SHA; staged signed APK as untrusted runner data; matched independent root receipt with `https_verified=true`; wrote owner URL to unpublished draft and read it back successfully. Publication verified; GitHub is not download endpoint.
- Manual trigger `.github/deploy/a1-owner-download-request.json`: `run_id=45854781668`, `attempt=1`, `release_id=459645155`. Legacy direct SSH workflow `.github/workflows/android-a1-owner-floki-download.yml` remains disabled `if: false`; never re-enable.
- Existing isolated runner `celikom-ci-smoke-only`; host spool `/srv/celikom/ci-runner/runner/celikom-a1-signed-spool`; runner view `/home/runner/celikom-a1-signed-spool`. Root-only consumer `/usr/local/lib/celikom-a1-signed-owner/consumer.py`, root timer/service `celikom-a1-signed-owner.timer` / `celikom-a1-signed-owner.service`, restricted receiver `/usr/local/sbin/celikom-a1-apk-receive`. Root receipt path `/srv/celikom/ci-runner/runner/celikom-a1-signed-spool/receipts/a1-45854781668-1.json`. Contains capability URL — confidential.
- No changes to stable Android/Windows, Nginx, API, root consumer or server security were necessary for BETA20 delivery.

## Why this beta was built; next step

- BETA19 Honor50 user diagnostic reported approved signed grant and alternate DataSource open/read, but the owner **did not hear the alternate audio**. `AUDIO_STAGE_B_STATUS=NOT_CONNECTED` is a permanently literal legacy status and is not the reason. No real current decoder/PCM proof.
- BETA20 fixes evidence-backed **first constructed factory instance vs first actual open() instance** mismatch. Fix commit `de786609ea256c43edda3f4992adb46f6da09651`: object identity and immutable creator/factory provenance are preserved and grant is armed on first real source open; touched sibling hard-rejects mixing. JVM regression checks two factory-created instances, wrong object, touched sibling. **Still not acoustic proof.**
- Owner installs BETA20 *over* BETA19 (no data removal), listens to Ramil «Ау» track `144530503`, album `38902809`, at 00:43–00:54, then returns TXT. Require real audible confirmation in addition to `AUDIO_EXO_FIRST_OPEN_ARM`, `DATASOURCE_ARMED`, `AUDIO_OPEN` and `AUDIO_READ`.
- If a future version is needed, prove root cause in diagnostics, fix experimental Android only, run native/JVM and signer/provenance checks, update manual request to the exact successful source run and draft release, and deliver **only** via signed Floki spool and independent root receipt. Never use hosted-runner direct SSH or raw GitHub download URLs.

---

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

## 25 November — receiver rejection after trusted APK identity check

Owner executed surgical recovery `f2bb9a516eda27de9af181fffcb5ae9021e64abd`. It installed fixed root consumer and root journal showed `A1_ROOT_SIGNER_AND_PACKAGE_VERIFIED`. Then root attempted `runuser -u celikom-deploy -- /usr/local/sbin/celikom-a1-apk-receive` and received exit 1; the old root wrapper hid captured receiver stderr, so no exact reason is proven. The owner inspected the entire unprivileged receiver (Python), including metadata schema and 2 GiB hard cap. **Owner's verified directory identities:** `/srv/celikom-a1-downloads` root:root 0711, `files` celikom-deploy:celikom-deploy 0711, `receipts` celikom-deploy:celikom-deploy 0700; these are correct for its documented contract. Owner **stopped** `celikom-a1-signed-owner.timer` to avoid repeated failing attempts. Do not change ownership, directory permissions, receiver validation or server isolation by guess.

Root consumer changed at commit `aabb755632d6b4073c551be1c1dec8ed61101e7f`, blob `547babe434317a6790d26a64891b1085c3f7aa21` to emit receiver exit code and **redacted** stderr to the root journal, retaining all signing/metadata/HTTPS validations. Added offline regression test for token redaction. Fresh-install bootstrap pins updated. Root-only diagnostic installer `.github/scripts/floki-a1-receiver-diagnostic-install.sh` at commit `f80cb31fc6dd0f868353875128d755c9f4613da8`, blob `b59472f3da3a63ba3bd7a35c8de1badcc7860a69`, validates installed consumer SHA and fetched blob, atomically updates only root consumer, starts A1 service once, logs **the concrete receiver reason** if it fails, and **leaves A1 timer stopped on failure**. If it succeeds and trusted BETA16 receipt exists, it restarts timer. This exact diagnostic version has **not yet been activated on server**.

**Next:** run that pinned installer from trusted root session and analyze `A1_ROOT_RECEIVER_STDERR` before any further fixes. BETA16 still **not confirmed publicly available**.

## Definitive 25 November blocker: runuser EPERM under NNP — direct child credentials

After running pinned root diagnostic `f80cb31fc6dd0f868353875128d755c9f4613da8`, trusted journal recorded **`A1_ROOT_SIGNER_AND_PACKAGE_VERIFIED`** then **`A1_ROOT_RECEIVER_STDERR runuser: cannot set user id: Operation not permitted`**. This is not an APK/signing/metadata/receiver-directory problem: `runuser` could not change identity *before the unprivileged Python intake ran*. Timer remained deliberately stopped.

Corrected trusted consumer `.github/scripts/floki-a1-root-signed-spool-consumer.py` at commit `28a6d279c6c5cfe481ef776203a91391ed868839`, blob `338221072cf4f65e03467e94fc753a1bf4c9eec6`. Root parent opens root-private intake fd, then Python `subprocess.run([RECEIVER], user=pwd.getpwnam("celikom-deploy").pw_uid, group=...pw_gid, extra_groups=[])` drops child identity **before exec** without util-linux runuser/PAM. Certificate, provenance, receiver, size, SHA, HTTPS validations unchanged. Tests now exercise exact child identity and redact stderr when receiver fails.

The hardened root service keeps `NoNewPrivileges=yes` and adds *only* `AmbientCapabilities=CAP_SETUID CAP_SETGID` so the credential drop is permitted even where default root service capability set is insufficient. No other service, SSH, nginx, receiver ownership or CI runner privileges change. Fresh bootstrap pins were updated at commit `a279bd3877c4f942613b3cfe5e1e940b01939a2c`. One-time trusted recovery script at commit `1782d4dd696e9d73990be40eb4c8d920a89bfa9c`, Git blob `c4f33cecf49065f62a6aef5eb823e809babe91b0`, ensures expected installed consumer blob, pins new consumer blob, writes only A1 unit drop-in, reloads systemd, tests NNP stays enabled and verifies BETA16 root receipt before restarting timer. Timer stays stopped on any failure.

Android A1 spool CI was retriggered by `e9eedf1144b228ca6e99876d92b652b898b3660d` to exercise upgraded offline tests. **Final live deployment and HTTPS acceptance not yet confirmed.** Next administrator step is the pinned root recovery; don't rebuild APK or restart entire bootstrap.

## Owner acceptance — BETA16 published on FlokiNET (25 November)

Owner executed trusted UID-drop repair at source commit `1782d4dd696e9d73990be40eb4c8d920a89bfa9c` (pinned repair blob `c4f33cecf49065f62a6aef5eb823e809babe91b0`). The root script emitted:

```text
A1_ROOT_BETA16_RECEIPT
{"attempt":1,"https_verified":true,"name":"CELIKOM-A1-RAMIL-AU-BETA16-HONOR50-20261125.apk","run":45652314715,"sha256":"5faf46740dce159aee6a04bee3020aba046f1ae7c61bf9e53e649d4fc4bb3035","size":71585772,"url":"[OWNER_CAPABILITY_URL_OMITTED]"}
A1_ROOT_BETA16_PUBLICATION_AND_TIMER_READY
```

**Delivered:** BETA16 is published from FlokiNET, with root verification of APK signer/package, size, digest, and HTTPS GET; independent root receipt is recorded and Android publisher timer reactivated. GitHub is no longer the APK download endpoint. The link is a private **owner capability URL**; do not advertise as public stable feed.

**Not yet accepted:** owner installation/listening on Honor 50, actual audible Ramil «Ау» substitution and corresponding diagnostics, and a future fresh Android build traversing this route automatically. Keep those acceptance stages separate; success of publication does not prove replacement acoustics or customer auto-update.


## 26 November — BETA17 build accepted; delivery returned to the trusted Floki spool

- Exact Android source run: `45814198959`, attempt 1, branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Native ARM13 75-second publisher-first gate and JVM issuer/proxy gate passed. The native gate is packaging/startup evidence only; `acoustic_replacement_proven=false`.
- Existing unpublished draft: release ID `459356293`, tag `celikom-a1-owner-45814198959-1`. APK `CELIKOM-A1-RAMIL-AU-BETA17-HONOR50-20261126.apk`, size `71589868`, SHA-256 `62c737c395ac185608531e81d55775e1bbbe152d3d390bead276ac233e833019`. Original package and owner signing certificate independently verified in CI.
- Legacy hosted-runner direct SSH delivery workflow `.github/workflows/android-a1-owner-floki-download.yml` is now disabled (`if: false`). Its retry hung at the remote intake stream and ended with exit 124; do not use this route or repeat the upload.
- Supported path is the existing isolated data-only runner spool plus root-owned verifier/timer. The spool workflow was adapted for the public repository while keeping APK bytes in the isolated spool, resolving the exact draft by immutable release ID, and retrieving the owner URL only from the root-written receipt. Capability URLs must never appear in public Actions logs or summaries.
- At the time of this entry, run `45819035079` was waiting for the root receipt. **This intermediate status is superseded by the completed-delivery section below**; the run later completed successfully and the receipt/draft readback were verified.
- If the root receipt does not appear before the workflow's 12-minute wait expires, diagnose only the existing `celikom-a1-signed-owner.service` / timer and its journal. Do not alter Nginx, API, receiver permissions, SSH access, Windows, stable Android, or the root consumer's security checks by guess.
- After owner link is retrieved, owner installs BETA17 over BETA16 on Honor 50 and tests Ramil `144530503`, album `38902809`, 00:43–00:54, then returns TXT. Audio replacement remains unproven until the phone's diagnostic confirms datasource/audio open/read and audible substitution.


### BETA17 owner delivery completed — 26 November

- Isolated Floki spool workflow run `45819035079` completed **success**. Exact BETA17 data staged as `a1-45814198959-1`; root-written receipt was found and matched run, attempt, filename, size and SHA-256, with `https_verified=true`.
- Root consumer had already independently checked the original signing certificate/package, uploaded through the existing restricted receiver, and verified external HTTPS response size and SHA-256. The workflow then stored the capability URL in the unpublished owner draft and successfully read it back: `A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED`.
- BETA17 is now **delivered to the owner**. Exact APK: `CELIKOM-A1-RAMIL-AU-BETA17-HONOR50-20261126.apk`, 71,589,868 bytes, SHA-256 `62c737c395ac185608531e81d55775e1bbbe152d3d390bead276ac233e833019`. The capability URL is intentionally not copied into public documentation or Actions logs.
- This is delivery acceptance only. The ARM13 gate is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; no claim of audible substitution. Next: install over BETA16 on Honor 50, test Ramil `144530503`, album `38902809`, 00:43–00:54, return diagnostic TXT. Do not alter stable Android or Windows.
