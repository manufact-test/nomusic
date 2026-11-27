# BETA29 NAV50 — alternate DataSource to live renderer correlation

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Current result — BETA29 delivered; phone diagnostic pending

BETA29 NAV50 was built, signed and delivered through the existing trusted Floki/root route. The owner has the direct HTTPS link from `celikom.com`. The next step is to install BETA29 over BETA28, run the two documented track tests, and provide a fresh TXT diagnostic. No BETA29 phone diagnostic has been reviewed yet.

- Owner/export run: `46061697450`, attempt 1 — SUCCESS.
- Build source commit: `1afa88c78b5b3a3063fac5176f1152a95dcdf962`.
- Floki manual run: `46064236455`, run 33 — SUCCESS; job `140727455245` — SUCCESS.
- Independent root-owned receipt and live HTTPS readback were verified. The final workflow marker was `A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED`.
- Private draft release `461031098` remains unpublished.
- APK: `CELIKOM-A1-RAMIL-AU-BETA29-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `5ae5c75a10daff02910fa5c2a8b4a10e0b02e28df2bfe6d1461d80337975b459`.

The root consumer verifies HTTP 200, Android APK content type, exact byte count and SHA-256, the root-owned receipt, and the unpublished draft readback. The capability URL is deliberately not stored in this document or repository.

BETA28 evidence below is retained as the baseline that motivated NAV50. It does not establish that the current BETA29 phone test has occurred, and it does not prove audible replacement.

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

## CI and delivery status

- Renderer observer JVM run `46060063393` — SUCCESS. `NativeRendererStreamEvidenceTest`, `NativeExoAlternateByteRouteTest`, and `NativeRamilTrackOnlyLineageTest` passed, including NAV50 same-source/current-period and mismatch assertions.
- Owner preflight run `46060063423` — SUCCESS. ARM13 native main 75s verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; persistent owner signer verified and update-existing mode confirmed. It remains a stability/signing gate only: `stage_a=NO_GO`, `audio_or_account_tested=false`, `stage_b_current_player_album_edition_attested=false`.
- Clone-alone run `46060063402` — SUCCESS. Verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`; `audio_or_account_tested=false` and `stage_b_current_player_album_edition_attested=false`. Stability gate only, not product/audio proof.
- BETA29 owner export run `46061697450`, run 500, attempt 1 — SUCCESS.
- BETA29 Floki manual delivery run `46064236455`, run 33 — SUCCESS; job `140727455245` — SUCCESS.
- Duplicate push-triggered Floki run `46063409036` was cancelled by the concurrency group; it is not the successful delivery run.
- Draft release `461031098` remains unpublished. Exact APK metadata and root-verified delivery are recorded above.

## Next action — inspect the BETA29 phone diagnostic

The owner installs BETA29 over BETA28 without uninstalling CELIKOM or clearing app data/cache, checks CELIKOM status, and if needed uses the long-press recovery menu and explicit `Войти` action. Then tests:

1. Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
2. The second song that previously had leading gaps.
3. Exports a fresh TXT after both tests.

When the TXT arrives, correlate all NAV50 counters per exact track and selection generation. Interpret the exact same-current-period non-EOS match as proof only that alternate bytes reached the active Exo source path, not proof of audible output. Choose the next engineering step from the observed boundary. Do not build another APK before this analysis.

## Guardrails

- No second player or new audio architecture.
- No audio route, source-selection, codec, transcoding or asset changes without diagnostic evidence.
- No changes to server, catalogue, signed-grant authorization, Windows, stable Android or OTA without direct evidence.
- Do not infer audible replacement from CI, `AUDIO_READ`, or a NAV50 same-source counter alone.
- Keep owner drafts unpublished. Any future owner APK must use the existing trusted Floki/root process; never fabricate or expose a capability URL.
