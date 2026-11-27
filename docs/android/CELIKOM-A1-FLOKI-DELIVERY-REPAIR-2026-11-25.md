> **LATEST DELIVERY BLOCKER — 28.11.2026 01:10 local:** BETA30 source/export and private draft are intact, but Floki delivery is blocked by both self-hosted runner slots accepting jobs without starting any workflow steps. Do not rebuild BETA30, publish GitHub APK assets, or bypass the trusted root consumer.
>
> - Original Floki run `46070217462` attempt 1 failed on `celikom-floki-ci01`; GitHub job record had `steps=[]`, and the log blob was unavailable. No root receipt or owner URL was verified.
> - Rerun attempt 2 was assigned to `celikom-floki-ci02`, also with `steps=[]`; exact cancellation completed at 22:04:45Z.
> - Recovery push commit `84aa896b0712fd813201e8b300c124cdf966457d` changed the Floki concurrency group and request JSON to include exact draft release `461085315`. It also unintentionally triggered Windows integration CI because `.github/deploy/a1-owner-download-request.json` was missing from Windows workflow `paths-ignore`.
> - Windows CI job `140757205584` / run `46073960759` is assigned to `celikom-floki-ci01`, no steps. Floki run `46073960828` is assigned to `celikom-floki-ci02`, no steps.
> - Main commit `bbef018619777c203af60fc56ebc4e524eca2c41` adds the missing request JSON path-ignore to `.github/workflows/windows-w98-integration-ci.yml`. This is a CI trigger filter only; no Windows product code changed.
> - One-shot recovery workflow `.github/workflows/android-a1-recover-stalled-spool-beta30-runners-once.yml` is temporary. First run `46074184246` failed due to a jq argument bug; fixed in commit `bae2553ce410d10cfea6b2eb8f9e569dbdd38538`. Corrected recovery runs `46074244421` and `46074559911` succeeded and issued cancel + force-cancel requests for exact no-step jobs. GitHub still reports runs `46073960759` and `46073960828` IN_PROGRESS; cancellation does not immediately clear the runner-side stuck process.
> - Current main commit `80fbba443717e62e8fb6591cadbbd99ea3cad348` adds the exact second CI02 no-step Floki job to the temporary recovery script.
> - Both runner rows showed Active in the owner's screenshot, but both assigned jobs remain step-less. No root receipt, HTTPS readback or owner capability URL exists yet. Do not ask the owner to click runner controls; do not change runner host, server, SSH, root, Docker or production permissions.
>
> **Next:** wait for exact stuck jobs to settle/runner slots to recover; then rerun the trusted Floki stage on an available runner. Ensure the Windows workflow ignores `.github/deploy/a1-owner-download-request.json` (already fixed) so Android delivery no longer starts Windows CI. Verify root receipt + HTTPS HTTP 200/content type/size/SHA + unpublished draft URL readback before sending link. Delete the temporary one-shot recovery workflow after recovery. Keep all Android app source on the experiment branch.

> **LATEST — BETA30 owner draft created; trusted delivery pending (27.11.2026):** owner/export run `46070081916`, attempt `1` — SUCCESS. Fresh Android 13 ARM64 + ARMv7 native gate passed (`METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`); the targeted NAV51 Java regression passed in the owner JVM gate. Unpublished draft release `461085315`, tag `celikom-a1-owner-46070081916-1`. APK `CELIKOM-A1-RAMIL-AU-BETA30-HONOR50-20261127.apk`, 71,602,156 bytes, SHA-256 `e33c3e31721d76ee82df7554f0eddb311202566328eafcb50f3f0958b7b53dfe`. Main delivery metadata commit `fca0dd41fad0fdf91a71f82e1d1751ab2f7e2f8c` points the trusted Floki workflow at run `46070081916`/attempt `1` and includes the BETA30 workflow-run name. Stale JVM run #260 (`46068440633`) is now CANCELLED; both self-hosted runners show Active. Floki run #34 (`46070217462`) is now IN_PROGRESS at `stage-verified-signed-apk`. **No root receipt or live HTTPS readback yet; do not send any link.** See `docs/android/NEXT-CHAT.md` for runner status and next steps.


## Historical checkpoints — BETA28 and earlier

> **BETA27 delivery complete (27.11.2026):** Floki spool workflow `46048173341` completed SUCCESS. Independent root receipt, live HTTPS readback and unpublished draft link readback all passed. Direct `celikom.com` URL delivered privately; capability URL intentionally omitted from Git/docs/logs. BETA27 owner audio test is pending. This supersedes the earlier "delivery pending" checkpoint below.

## Historical delivery checkpoint — BETA27 (27.11.2026)

BETA26 was previously delivered and verified. BETA27 source workflow `46028046471` passed JVM and fresh Android 13 native-launch checks. APK metadata:
- `CELIKOM-A1-RAMIL-AU-BETA27-HONOR50-20261127.apk`
- 71,598,060 bytes
- SHA-256 `5939d5f9c8dc7661c5eac64f06391bf06f854b1da79158dfacc2f41f74f918c1`
- persistent owner signer verified.

The trusted main request JSON now targets run `46028046471`, attempt 1, private draft release `460809106`. Floki spool workflow `46048173341` verified provenance, digest and package signer and staged the APK. At the last checkpoint it was waiting for the independent root-owned HTTPS receipt. Do not treat staging as delivery. Do not send any link until the root receipt and live celikom.com HTTP 200 / content-type / exact size / SHA-256 checks pass and the unpublished draft readback confirms the same URL. No GitHub APK link may be sent to the owner.

BETA27 CI verdict is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; `acoustic_replacement_proven=false`. The owner still must install and hear the alternate sound.

Continuation: `docs/android/NEXT-CHAT.md` and `docs/android/CELIKOM-A1-BETA27-EXACT-DESCRIPTOR-FIRST-OPEN-2026-11-27.md`.

# CELIKOM A1 — Floki verified owner APK delivery repair

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Current delivery workflow: `.github/workflows/android-a1-owner-floki-spool.yml`

## Purpose

This record documents the verified delivery of the BETA26 owner APK through the existing trusted-main Floki spool. It does not describe or prove successful audio replacement.

The owner cannot download APKs from GitHub on the phone. Every owner-phone APK must be delivered through the direct HTTPS capability URL on `celikom.com`, obtained from the unpublished owner draft only after the independent root receipt and live HTTPS readback pass.

## BETA26 source and artifact identity

- Android source branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Source commit: `bcb5d9ccee56b2e8bcc5493c12514c07f342ee6b`.
- Source/export workflow run: `46014952782`, attempt `1`, successful.
- Unpublished owner draft release ID: `460707648`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA26-HONOR50-20261127.apk`.
- Size: `71,598,060` bytes.
- SHA-256: `43e5bb00eabde955eff8e2b25b76986a29198fa3f7ca0512cc55ff234b245888`.
- Original application package and signing certificate were independently verified.
- Install mode: update existing installation; do not uninstall or clear app data/cache.

## Exact trusted-main request — historical BETA26 snapshot

At the time of the BETA26 delivery record, `.github/deploy/a1-owner-download-request.json` on `main` contained the following. This is historical and was later superseded by the BETA29 request (`run_id=46061697450`, `attempt=1`, `release_id=461031098`):

```json
{
  "attempt": 1,
  "release_id": 460707648,
  "run_id": 46014952782
}
```

The request is updated on `main` to invoke the `push.paths` trigger of the trusted spool workflow. Do not rely on the workflow's `workflow_run` filter for this build: it still names an older BETA13 workflow title.

## Floki run history and verified result

- First spool run: `46017089409` — cancelled when the concurrency group was superseded.
- Retry spool run: `46018546776`, attempt `1` — failed before any job step ran on `celikom-floki-ci02`; no root cause was established from that attempt.
- The failed job was re-run without changing the APK or bypassing the delivery path.
- Successful retry: run `46018546776`, attempt `2`, job `140596788844`, runner `celikom-floki-ci01` — SUCCESS.

The successful retry completed all workflow stages:
1. Local data-only spool regression tests and root consumer compile checks.
2. Exact successful Android source workflow, attempt, branch and private draft provenance resolution.
3. Java/Android SDK setup.
4. Independent APK signer and package verification.
5. Immutable data-only staging into the Floki spool.
6. Independent root consumer verification of provenance, APK size and SHA-256.
7. Existing trusted receiver promotion.
8. Live HTTPS readback: HTTP 200, expected APK content type, exact byte count and SHA-256.
9. Root receipt creation with exact run/attempt/name/size/hash and `https_verified=true`.
10. Update and readback verification of the unpublished owner draft.
11. Temporary runner APK/metadata cleanup.

The exact direct owner URL was retrieved from the unpublished draft and sent privately in the preceding chat. The capability token and URL are deliberately not reproduced in this file, in Git, in workflow logs, or in public summaries.

## Security constraints — mandatory for future APK deliveries

- Use only `.github/workflows/android-a1-owner-floki-spool.yml` and the trusted-main JSON request route.
- The APK is staged as untrusted data; trusted main workflow code executes. The isolated runner does not publish or execute APK contents.
- The independently installed root-owned consumer validates source provenance, signing certificate, package ID, file type, size and SHA-256 before handing data to the existing receiver.
- Require the matching root-owned receipt and successful live HTTPS size/hash readback before retrieving the URL.
- Read the actual `A1_OWNER_DOWNLOAD_URL` from the unpublished draft; never synthesize or guess a URL.
- Keep the owner draft unpublished.
- Never expose the capability URL/token in Git, documentation, Actions logs/summaries, public messages, or artifacts.
- The legacy direct-SSH workflow is disabled. Do not re-enable it.
- Do not bypass the root consumer, alter server permissions, weaken Floki security, or introduce a new delivery mechanism.

## BETA30 NAV51 — owner draft ready, Floki delivery pending (27.11.2026)

- Source/export workflow run `46070081916`, attempt `1` — SUCCESS.
- Source branch commit: `aef40439586304fd57dabcbf20dfcce3af52a181`.
- Unpublished owner draft: release `461085315`, tag `celikom-a1-owner-46070081916-1`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA30-HONOR50-20261127.apk`, 71,602,156 bytes.
- SHA-256: `e33c3e31721d76ee82df7554f0eddb311202566328eafcb50f3f0958b7b53dfe`.
- The persistent owner signer, package verification, owner JVM regression and fresh Android 13 ARM64 + ARMv7 native gate passed. Verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- Main metadata commit `fca0dd41fad0fdf91a71f82e1d1751ab2f7e2f8c` changed only the Floki workflow filter and trusted request JSON. It points to run `46070081916`, attempt `1`; no app source was merged to main.
- JVM run `46068440633` / #260 is COMPLETED-CANCELLED; its `nav17-owned-observer-no-vendor-code` job is cancelled. Both self-hosted runners showed Active in the owner's screenshot.
- Floki push run `46070217462` / #34 is now IN_PROGRESS, job `stage-verified-signed-apk` (`140745086840`). No readable job log is available yet while it is running.
- Do not cancel the Floki stage, alter runner settings, or send a GitHub release URL. Delivery remains pending until the root-owned consumer verifies the exact source provenance, signer, package, size and SHA-256, writes the matching receipt, and live HTTPS readback returns HTTP 200 with the expected content type, exact byte count and hash. Only then read the real `A1_OWNER_DOWNLOAD_URL` from the unpublished draft and deliver privately.
- If the queued Floki job fails before any step runs, retry the existing trusted Floki job without rebuilding or changing the APK. Do not bypass the root consumer or alter server permissions.

## BETA26 outcome and limitation (historical)

**BETA26 delivery is complete and verified.** The owner received the direct `celikom.com` link privately.

This is only an APK delivery result. The Android CI verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; `acoustic_replacement_proven=false`. Actual playback and audible replacement must be established by the owner's BETA26 phone diagnostic and listening test.

For the current diagnostic and code handoff, see:
- `docs/android/NEXT-CHAT.md`
- `docs/android/CELIKOM-A1-BETA26-OWNER-DIAGNOSTIC-NEXT-STEPS-2026-11-27.md`


## 2026-11-27 — BETA29 manual trigger fallback (completed)

A manual `workflow_dispatch` fallback was added because the request-file commit made through the GitHub connection did not start Actions automatically. The owner then launched the existing workflow manually. Successful run `46064236455` completed the same root-owned receipt, live HTTPS and unpublished-draft checks. No further manual run is needed for BETA29; see the latest checkpoint at the top of this document.

## 2026-11-27 — BETA29 delivered to owner

- Manual Floki spool run `46064236455`, run number 33 — SUCCESS.
- Job `140727455245` — SUCCESS.
- Independent root-owned consumer verified signer/provenance, receipt ownership, live HTTPS HTTP 200, APK content type, exact size and SHA-256, and unpublished draft readback. Final marker: `A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA29-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `5ae5c75a10daff02910fa5c2a8b4a10e0b02e28df2bfe6d1461d80337975b459`.
- Draft release `461031098` remains unpublished. Its real `A1_OWNER_DOWNLOAD_URL` was read back and delivered directly to the owner. Never copy the capability URL into Git/docs/logs.
- Duplicate push run `46063409036` was cancelled by concurrency; the successful manual run above is the delivery proof.

Owner installs over BETA28 without uninstalling or clearing data, tests the target and second song, and exports TXT. Do not claim audio replacement until phone evidence confirms it.
