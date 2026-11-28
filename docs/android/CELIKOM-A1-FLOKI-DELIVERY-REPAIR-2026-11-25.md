# CELIKOM A1 — trusted Floki owner APK delivery procedure

Last verified: 2026-11-28  
Repository: manufact-test/nomusic

This file is a short operational procedure, not a chronological runner incident log. Current Android state is in docs/android/NEXT-CHAT.md. Read this file only when an owner APK actually needs delivery or a delivery failure occurs.

## Required delivery route

Use only the existing trusted-main workflow:
- Workflow: .github/workflows/android-a1-owner-floki-spool.yml
- Request file on main: .github/deploy/a1-owner-download-request.json

Start delivery only after the exact Android source/export workflow has succeeded and created the unpublished owner draft. The request JSON must point to the exact successful source run, attempt and draft release ID. It is distribution metadata only; it does not merge Android app code into main.

The trusted Floki workflow must:
1. Resolve the exact successful source run, branch, commit and unpublished draft.
2. Verify APK provenance, expected package, original installed-app signing certificate, exact size and SHA-256.
3. Stage only the immutable verified APK as untrusted data.
4. Wait for the independent root-owned consumer.
5. Verify the root receipt matches the exact source run, attempt, filename, size and SHA-256.
6. Require https_verified=true and successful live HTTPS readback with HTTP 200, expected APK content type, exact byte count and exact SHA-256.
7. Patch and read back the unpublished owner draft, confirming exactly one matching owner capability URL.

The owner URL is valid only after all checks above pass. Retrieve the actual URL from the unpublished draft and send it privately.

## Security rules

- Keep the owner draft unpublished.
- Never send a GitHub release or asset URL to the owner.
- Never synthesize, guess, log, commit or copy the capability URL/token into Git, docs, Actions summaries, logs or public messages.
- Do not bypass the root consumer or its receipt.
- Do not change server permissions, runner permissions or the delivery architecture.
- The legacy direct-SSH workflow stays disabled.
- A successful staging step alone is not delivery. Require the root receipt, live HTTPS readback and draft readback.

## Stalled no-step runner handling

If a Floki job is accepted but has steps=[]:
1. Inspect the exact run/job and confirm it is genuinely the no-step condition.
2. Do not cancel unrelated jobs or restart runners based only on an Active label.
3. Use the existing narrowly scoped one-shot recovery workflow only for the exact stalled job when required.
4. Wait for the runner slot to clear, then retry the same already verified APK through the trusted Floki path.
5. Do not rebuild the APK merely because delivery was retried.
6. Never bypass root verification or weaken security to make delivery faster.

## Latest verified delivery

BETA33 owner APK delivery completed on 2026-11-28:
- Android source/export run: 46132374238, attempt 1 — SUCCESS.
- APK: CELIKOM-A1-RAMIL-AU-BETA33-HONOR50-20261128.apk.
- Size: 71,602,156 bytes.
- SHA-256: 41e0abea857cd6159edf20e38b25e9e594621fdda86da68bc0471aadc839fd61.
- Floki spool run: 46133753704, run 41 — SUCCESS.
- Final marker: A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED.
- Root receipt confirmed https_verified=true.
- Owner capability URL is stored in the unpublished private draft and is intentionally not reproduced here.

No further BETA33 build or delivery run is required. If the owner has not received the link, retrieve the existing URL from the unpublished draft and send it privately. The remaining gate is owner installation and real phone/audio acceptance, not delivery infrastructure.
