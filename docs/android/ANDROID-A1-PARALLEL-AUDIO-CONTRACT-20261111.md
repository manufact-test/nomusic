# CELIKOM Android A1 — helper B, independent audio-source contract (#42)

**Scope:** isolated source decision and deterministic lifecycle tests. **Status: preparation only.** Android A1 Stage A native clone still exits MAIN with EXIT_SELF(0); no native player start, no audible replacement, no owner-approved build. Stage B/custom injector remains locked. No changes to publisher app, native loader, production backend, Android Test.50, Windows W61 or extension.

## Files and execution

- android/native-audio-contract/source-contract.mjs — pure ESM source-only state machine. No player, decoder, network stack or runtime hook.
- android/native-audio-contract/source-contract.test.mjs — run: node --test android/native-audio-contract/source-contract.test.mjs
- .github/workflows/android-a1-b42-source-contract.yml — isolated Node 22 checks; unchanged A1 ARM native boot CI.
- This document is the only helper-owned documentation.

## Verified read-only sources

| Component | Existing behavior | Limitation |
| --- | --- | --- |
| PHP server/src/Application/ResolveService.php | resolve("yandex", exactDecimalTrackId, access, supportsM4a) returns found, replacement_id, relative audio_url, duration_ms, mime_type, version, expires_at (Unix seconds); HMAC includes replacement ID/version/expiry and optional session sid | Does not return album/edition identity or an explicit approved/entitled assertion. Null access is not proof of paid entitlement. |
| PHP server/src/Application/AudioTokenService.php | HMAC v2 with sid, TTL 60–1800 seconds (default 600) | Client must not manufacture or extend the signed grant. |
| PHP server/src/Http/AudioController.php and ByteRange.php | HEAD 200 with MIME, length, Accept-Ranges bytes and quoted SHA-version ETag; GET 200 full, GET 206 partial; 416 with Content-Range bytes */size; If-Range mismatch returns full 200 | Only one byte range; 200 must not be mistaken for successful partial seek. |
| Windows W61 SourceSwapGate.cs, w15/source-controller.mjs, w22/native-resource-adapter.mjs and w60/current-source-refresh.mjs | Exact ID gate, HTTPS grant validation, generation/abort, in-place source refresh on Start/Stop | Windows reloadEntity("QUALITY_CHANGE") is NOT a proven Android API or native host hook. |
| Extension extension/src/player/core.ts | Decimal track identity, catalog and playback events | Fuzzy title/artist matching can help discovery but must NOT authorize a native audio replacement. |

## Trust and host boundary (NOT implemented here)

Future **authorized** host adapter supplies:
1. resolve({trackId, albumId, editionId, durationMs}, abortSignal): authenticated CELIKOM lookup, independent session/entitlement verification, trusted normalized grant.
2. probeHead(signedAbsoluteAudioUrl, abortSignal): authorized HEAD of existing CELIKOM audio resource, returns status and headers.
3. now(): epoch milliseconds and optional timers/onEvent(code).

The **raw PHP resolve response is not a validated normalized grant**. Only after confirming found, active/approved catalog state, exact Yandex track identity, verified CELIKOM session entitlement at resolve time and that signed sid is bound to the intended verified session, may an adapter map audio_url against its trusted configured API origin; expires_at becomes expiresAt * 1000 and duration_ms becomes durationMs. The source model will check format and expiry but cannot independently verify the server HMAC or upstream account. The backend handles HMAC and access; never fake a verified entitlement. API remains unchanged.

**Real blocker:** current PHP resolve does NOT return album/edition. If host supplies albumId or editionId, the adapter needs independent authoritative catalog evidence for exactly that identity. Without it, reject and leave original; do NOT invent fields or infer identity from title/album cover. Contract tests cover this rejection.

Normalized shape expected *after* trusted adapter verification: trackId, albumId, editionId, approved=true, entitled=true, version (positive integer), durationMs, mimeType, expiresAt (epoch milliseconds), audioUrl (HTTPS absolute signed URL). This is an interface definition, NOT an actual signed grant.

The gate requires exact current track and matching known album/edition, optional pinned replacement version, approval/entitlement flags, origin matching incl. port, audio path, only the unique token/expires/sid parameters, no fragment or URL credentials, expiry >30 seconds and <=30 minutes, valid MIME and duration difference <=2000ms. The sid is intentionally mandatory for this entitlement-bound Android model. Server must independently check the signed session again on each Range request.

A HEAD probe must return 200, matching supported MIME, positive content length, Accept-Ranges bytes and strong quoted ETag. Failing any check returns ORIGINAL: existing native host remains in control, no host playback commands issued.

## State machine

- observeTrack creates a generation for the exact track, album/edition, duration and native transport snapshot. next and myWave always cancel old work (including repeated same track ID), even when following queue is unknown. Unknown identity stays original.
- enable reevaluates current track. disable and preferOriginal revoke all earlier replacement decisions. **Actual same-track source reload with preserved position/pause is the future native host's responsibility**, not implemented by this model.
- pause/resume/seek only update transport snapshot. There is no second audio engine, separate playback clock, MediaPlayer/AudioTrack/decoder or time-to-byte estimator.
- requestSource uses generation plus request sequence, AbortSignal and bounded deadline (1250ms default). Returns REPLACEMENT validated ticket, ORIGINAL current-track fallback, or IGNORE for outdated async result. IGNORE must never cause native source selection.
- Always call isCurrent(decision) right before native application and after asynchronous work. commit(decision, applied) only tracks **source selection**; SOURCE_SELECTED_NOT_AUDIBLE_VERIFIED is explicitly NOT proof of audible playback.
- ended/dispose invalidate; no prefetch or guessed Next/Моя волна source selection. Any future prefetch must remain generation scoped and never activate guessed audio.
- On wrong identity, missing album/edition attestation, invalid/grant expiry, entitlement denial, HEAD failure, errors, timeout or network loss: continue original, do not freeze native playback.

## HEAD, GET, Range and seek

- buildByteRangeHeaders(start, end?, etag?) uses byte indices only; calculating byte position from native seek is host responsibility. Supports If-Range only with strong ETag.
- validateRangeResponse accepts 206 only when Content-Range start/end/total, response length and ETag match request and HEAD witness; 416 bytes */total means unsatisfiable; 200 is NOT accepted as partial (may mean If-Range mismatch).
- Host must revalidate generation and signed URL before attaching any stream. No logging or storage of signed URLs, account secrets, tokens or sid. onEvent emits enum-like codes only, no track IDs. The trusted host boundary necessarily receives signed URL for current source and must not put it in telemetry.

## Mandatory handoff to A

1. Review helper PR into experiment/android-native-a1-lspatch-clone-loader0-20261111; helper never merges or edits that branch.
2. Run isolated Node tests and whole A1 CI from current integration head. Treat missing backend album/edition attestation as a real blocker; do not silently turn it into success.
3. Implement only a narrowly scoped, authorized native host adapter after Stage A native startup and security gates permit it. Do not port Windows webpack/Yandex APIs as assumed Android APIs.
4. Owner audible validation on actual native host required (replacement/original, Next/MyWave, same-track Start/Stop, pause/seek/expiry/fallback). Stage A stays NO-GO until approved; no custom Stage B injector.

**Release classification:** B42 preparation can test PASS while Android A1 product remains NO-GO.


## Lead A review hardening after PR #43 integration

The main A1 integrator accepted the helper's source-only contract, then tightened the same module before allowing any future host adapter:
- REPLACEMENT decision has private object identity tied to the issuing source-contract instance. Manually fabricated tickets or tickets from a second contract are rejected.
- commit consumes each ticket once (whether native application succeeded or failed); repeated callback cannot double-apply an old source.
- Every HTTP Range 206/416 classification requires a valid previously verified HEAD size/strong ETag. 416 must match the witnessed total and genuinely be out of bounds.
- Extra deterministic tests prevent regressions. All remain pure contract tests; signed Yandex native host remains unintegrated and Stage A still NO-GO.
