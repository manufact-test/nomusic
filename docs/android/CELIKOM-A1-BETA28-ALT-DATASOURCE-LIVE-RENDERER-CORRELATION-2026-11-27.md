# BETA28 phone result — alternate DataSource to live renderer correlation

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Current result

BETA28 was delivered through the trusted Floki/root route and installed over BETA27. The owner reports that audible replacement still does not occur.

Latest phone diagnostic:
- `CELIKOM-A1-Diagnostics-1795806916651.txt`
- Diagnostic build marker: `A1_TRACKID_BETA28_OWNER_SESSION_RECOVERY_20261127`

Do not infer that the alternate audio asset is broken or in the wrong format. The phone diagnostic and the source code show that the limited BETA route returned positive alternate bytes through the original Exo DataSource read hook.

## What BETA28 actually proves

The diagnostic includes:
- `OWNER_ENABLED=ONE`
- `SIGNED_MPEG_READY=ONE`
- `OWNER_RESOLVE_APPROVED=ONE`
- `SIGNED_AUDIO_READY=ONE`
- `OWNER_AUDIO_RANGE_VALID=ONE`
- `DATASOURCE_ARMED=ONE`
- `AUDIO_OPEN=ONE`
- `AUDIO_READ=MANY`

In `ExitCallsiteWitness.java`, the `AUDIO_READ` counter is incremented only when `NativeExoAlternateByteRoute.readIfApproved(...)` returns a positive byte count. The route returns the bytes read from its approved alternate cursor. This is stronger than merely receiving a signed URL: the alternate bytes were returned through the original Exo DataSource hook.

However, this does **not** prove that this exact DataSource instance belongs to the MediaPeriod currently being rendered. The pre-prepare observer can see a period that is being prepared or prefetched; it is not by itself proof of current selection.

The codec/output counters are process-wide observations:
- `CODEC_CONFIG_MPEG=NONE`
- `CODEC_CONFIG_AAC=FEW`
- `CODEC_AUDIO_START=FEW`
- `PLATFORM_AUDIOTRACK_PLAY=FEW`

They are not joined to the exact alternate DataSource or the current track. Do not use them alone to conclude that MPEG is invalid or that AAC is decoding the alternate source.

The strict legacy `AUDIO_STAGE_B_STATUS CELIKOM_REPLACEMENT NOT_CONNECTED` is not the status of the separate owner-consented limited BETA route. The BETA-specific counters above are the relevant source-read evidence.

## Missing link identified

The phone diagnostic already observes a live audio renderer read and a current period/source lineage, but it does not join that current period's Track wrapper to the exact DataSource instance that was armed and returned alternate bytes.

Relevant renderer observations include:
- `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=FEW`
- `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MINUS4=FEW`
- `LIVE_PERIOD_DIRECT_LO96=FEW`
- `LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT=FEW`
- `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=FEW`
- `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH=FEW`
- `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=FEW`
- `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_NO_LINK=FEW`
- `PERIOD_ADAPTER_RENDERER_STREAM_MATCH=NONE`
- `PERIOD_ADAPTER_RENDERER_STREAM_UNAVAILABLE=MANY`
- `PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH=NONE`

The direct `Lo96` MediaPeriod path is observed, but the previous adapter-only witness cannot join it to the armed DataSource. The current PlaybackInfo period identity is also only observed with EOS unknown in this diagnostic. Therefore the BETA28 `AUDIO_READ` count cannot yet be attributed to the audible current track; it may be a prefetch or stale source generation.

## NAV50 diagnostic-only change

Source commit: `466eb2cd8b8de6ca6c6d3cff4cc1553cbe268f1d`

The patch adds a read-only identity join. It does not change the audio route, Yandex codecs, player, server, authorization, Windows, stable Android or OTA.

1. `NativeExoAlternateByteRoute`
   - Tracks positive alternate reads for the exact armed DataSource object.
   - Exposes a read-only source status: same source with positive alternate reads, same source armed but unread, different source, or no route.

2. `StageBAudioEvidence`
   - Adds `linkedSourceInstanceForCreatorOrBeta(wrapper)`.
   - Resolves the exact DataSource already linked to the original Track wrapper, including after open/read.
   - This is observation only; it cannot nominate or arm a source.

3. `NativeRendererStreamEvidence`
   - On the same live SLOT_B audio-renderer read callback, resolves the current period's Track wrapper to its exact DataSource.
   - Compares that DataSource by object identity with the route that returned alternate bytes.
   - Rechecks the holder source, live queue slot and current PlaybackInfo PeriodID before counting a current-period match.
   - Separates non-EOS, EOS-unknown, different-source, no-route and unresolved cases.

4. `ExitCallsiteWitness`
   - Wires the Stage B DataSource lookup and alternate-route status into the renderer observer.
   - Exports counters only; no URLs, tokens, track IDs or source objects are logged.

### New diagnostic counters

- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS`: strongest positive result. The current non-EOS renderer period is tied to the exact DataSource that has returned alternate bytes.
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_EOS_UNKNOWN`: same source/current-period identity, but EOS state is unknown; do not call this full proof.
- `LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD`: current renderer period resolves to a different DataSource than the armed alternate route; likely prefetch/stale generation or wrong source binding.
- `LIVE_RENDERER_ALT_SOURCE_ARMED_NO_READ_CURRENT_PERIOD`: the current period uses the armed DataSource, but no positive alternate read has been observed for it.
- `LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD`: current period has no matching active alternate route.
- `LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD`: current wrapper could not be joined to its exact DataSource.
- `LIVE_RENDERER_ALT_SOURCE_SLOT_OR_PERIOD_CHANGED`: holder/queue/period changed during the evidence check.

Interpretation:
- If the exact current non-EOS match is positive, the alternate bytes have reached the active Exo source path; investigate extractor/decoder/output next. Do not rebuild the source-selection path.
- If the active period has a different DataSource, fix the selection-generation/prefetch binding. Do not change codecs or audio assets.
- If the DataSource is unresolved, repair only the wrapper-to-factory-product identity witness.

## CI status

- Renderer observer JVM run `46060063393` — SUCCESS. It compiled and ran:
  - `NativeRendererStreamEvidenceTest`
  - `NativeExoAlternateByteRouteTest`
  - `NativeRamilTrackOnlyLineageTest`
  - The new NAV50 same-source/current-period and mismatch assertions passed.
- Owner preflight run `46060063423` — SUCCESS. ARM13 native main 75s verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; persistent owner signer verified and update-existing mode confirmed. It remains a stability/signing gate only: `stage_a=NO_GO`, `audio_or_account_tested=false`, `stage_b_current_player_album_edition_attested=false`.
- BETA29 export run `46061697450`, run 500, attempt 1, source `1afa88c78b5b3a3063fac5176f1152a95dcdf962` — IN_PROGRESS at the last checkpoint. This is the only intended BETA29 export candidate.
- Clone-alone workflow `46060063402` — SUCCESS. Verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`; `audio_or_account_tested=false` and `stage_b_current_player_album_edition_attested=false`. This is a stability gate only, not product/audio proof.
- Several intermediate export-trigger commits were made during the BETA29 filename migration. They may create older-name private drafts; do not deliver any of them. Only use run `46061697450` if its final draft contains exactly the BETA29 artifact name.

Wait for the owner ARM13 and clone-alone workflows to finish before exporting a new owner APK.

## Next action

If the remaining owner/clone gates pass, build a **diagnostic-only BETA29** containing NAV50. It must remain an unpublished owner draft and use the same trusted delivery process:
- owner signer/provenance checks;
- private spool;
- independent root-owned receipt;
- live `celikom.com` HTTPS verification;
- exact size/hash readback;
- actual `A1_OWNER_DOWNLOAD_URL` read from the unpublished draft.

The owner workflow exports on push only when the commit message contains `[export-beta-audio]` **and** the changed path matches its source/test path filter. A docs-only commit will not trigger it; use a comment-only change in an already included source path after all gates pass. Do not send a GitHub APK link. Do not publish the draft or bypass Floki/root verification.

The phone test for BETA29 is intentionally narrow: install over BETA28 without uninstalling or clearing data, reproduce the same Ramil / 10AGE — «Ау» test and the second song, then export TXT. The new counters decide whether the next change belongs in source selection or after the Exo DataSource read.

## Guardrails

- No second player.
- No audio transcoding or codec changes without evidence.
- No changes to server, catalogue, signed-grant authorization, Windows, stable Android or OTA.
- Do not claim audible replacement from CI or from `AUDIO_READ` alone.
