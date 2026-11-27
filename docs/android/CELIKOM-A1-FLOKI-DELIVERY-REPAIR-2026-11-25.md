> **Latest checkpoint — BETA28 (27.11.2026):** BETA28 source/export workflow `46049315766` SUCCESS; clone-alone ARM13 `46049315771` SUCCESS; renderer JVM `46049315695` SUCCESS. APK `CELIKOM-A1-RAMIL-AU-BETA28-HONOR50-20261127.apk`, 71,602,156 bytes, SHA-256 `2c5dee053f2634224f929113e94b5aafe5ca5492160ed16f8e267020b394555c`, persistent owner signer verified. Private draft release `460950166`. Trusted-main request commit `64a1f36a5d3fb6951f327e28864fd5a10440203b`; Floki spool run `46052141389` / job `140685817495` was still `in_progress` at last check, with no confirmed root receipt or live HTTPS readback. **BETA28 is built but not yet delivered. BETA27 remains latest delivered.** Continue only through existing trusted Floki root receipt and live celikom.com verification; never send GitHub link or guess URL. Full details: `docs/android/NEXT-CHAT.md` and `docs/android/CELIKOM-A1-BETA28-OWNER-SESSION-RECOVERY-2026-11-27.md`.

> **BETA27 delivery complete (27.11.2026):** Floki spool workflow `46048173341` completed SUCCESS. Independent root receipt, live HTTPS readback and unpublished draft link readback all passed. Direct `celikom.com` URL delivered privately; capability URL intentionally omitted from Git/docs/logs. BETA27 owner audio test is pending. This supersedes the earlier "delivery pending" checkpoint below.

## Current delivery checkpoint — BETA27 (27.11.2026)

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

## Exact trusted-main request

The current `.github/deploy/a1-owner-download-request.json` on `main` contains:

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

## Current outcome and limitation

**BETA26 delivery is complete and verified.** The owner received the direct `celikom.com` link privately.

This is only an APK delivery result. The Android CI verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; `acoustic_replacement_proven=false`. Actual playback and audible replacement must be established by the owner's BETA26 phone diagnostic and listening test.

For the current diagnostic and code handoff, see:
- `docs/android/NEXT-CHAT.md`
- `docs/android/CELIKOM-A1-BETA26-OWNER-DIAGNOSTIC-NEXT-STEPS-2026-11-27.md`
