# CURRENT HANDOFF — BETA28 tested; NAV50 live-renderer correlation added

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## What the next chat must do first

Read these documents in order:

1. `docs/android/NEXT-CHAT.md` (this handoff)
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md`
3. `docs/android/CELIKOM-A1-BETA28-OWNER-SESSION-RECOVERY-2026-11-27.md`
4. `docs/android/CELIKOM-A1-BETA28-ALT-DATASOURCE-LIVE-RENDERER-CORRELATION-2026-11-27.md`

BETA28 delivery is complete and the owner has tested it. Do not repeat its delivery workflow or ask for another diagnostic now. The owner reports no audible replacement on BETA28. The latest TXT is already available in the conversation as `CELIKOM-A1-Diagnostics-1795806916651.txt`.

The immediate engineering task is to finish the NAV50 owner/clone CI gates. If they pass, prepare a diagnostic-only BETA29 with the new exact DataSource-to-live-renderer counters. Do not change audio behavior before those counters identify the failing boundary.

## BETA28 delivery and phone result

- APK: `CELIKOM-A1-RAMIL-AU-BETA28-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `2c5dee053f2634224f929113e94b5aafe5ca5492160ed16f8e267020b394555c`.
- Persistent owner signer SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
- Private unpublished owner draft release ID: `460950166`.
- Trusted Floki spool workflow: `46052141389`, attempt 2 — SUCCESS.
- Independent root-owned receipt, live `celikom.com` HTTPS HTTP 200, APK content type, exact size and SHA-256, and unpublished draft readback were verified.
- The real owner URL was read from the draft and delivered in the previous chat. Do not reuse, reconstruct, or store its capability URL in Git/docs/logs.

Phone result: BETA28 installed over BETA27 without uninstalling or clearing data. Owner reports that audible replacement still does not occur.

## BETA28 source and prior successful checks

- Source commit: `895306cee0934e245aeda7aaa0ce95f3b609eff2`.
- Owner build/JVM: run `46049315766` — SUCCESS.
- Separate ARM13 clone-alone: run `46049315771` — SUCCESS.
- Renderer JVM: run `46049315695` — SUCCESS.
- Native launch verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- The CI verdict was explicitly not audio replacement proof.

## What the BETA28 phone diagnostic proves

The diagnostic includes:
- `OWNER_ENABLED=ONE`
- `SIGNED_MPEG_READY=ONE`
- `OWNER_RESOLVE_APPROVED=ONE`
- `SIGNED_AUDIO_READY=ONE`
- `OWNER_AUDIO_RANGE_VALID=ONE`
- `DATASOURCE_ARMED=ONE`
- `AUDIO_OPEN=ONE`
- `AUDIO_READ=MANY`

In the actual source, `AUDIO_READ` is incremented only when the approved alternate Exo DataSource read returns a positive byte count. Therefore alternate bytes were returned through the original Exo DataSource hook.

This still does not prove that the exact DataSource which returned alternate bytes belongs to the MediaPeriod currently rendered by Yandex. The pre-prepare hook can run for a period being prepared or prefetched. Codec and AudioTrack counters are process-wide and are not tied to that DataSource; do not conclude that the asset is broken or that MPEG/AAC mismatch is the cause.

The renderer diagnostic sees live SLOT_B audio reads and direct Lo96 period/source evidence, but BETA28 did not join the live period's Track wrapper to the exact DataSource object that the alternate route armed. See the NAV50 investigation document for the precise evidence and missing link.

## NAV50 diagnostic-only source change

Current source commit before the latest documentation-only handoff update:
`466eb2cd8b8de6ca6c6d3cff4cc1553cbe268f1d`.

NAV50 does not change the audio route, player, Yandex codecs, server, authorization, Windows, stable Android or OTA. It adds a read-only identity join:

1. `NativeExoAlternateByteRoute` tracks positive alternate reads per exact DataSource object and exposes a read-only identity status.
2. `StageBAudioEvidence.linkedSourceInstanceForCreatorOrBeta(wrapper)` resolves the exact DataSource already linked to the original Track wrapper, even after open/read. It cannot nominate or arm a source.
3. `NativeRendererStreamEvidence` checks the same live SLOT_B audio-renderer read callback, current PlaybackInfo PeriodID, holder source, and DataSource identity against the route that returned alternate bytes.
4. `ExitCallsiteWitness` wires the observer and exports counters only. No URLs, tokens, track IDs or source objects are logged.

New counters include:
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS`
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_EOS_UNKNOWN`
- `LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD`
- `LIVE_RENDERER_ALT_SOURCE_ARMED_NO_READ_CURRENT_PERIOD`
- `LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD`
- `LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD`
- `LIVE_RENDERER_ALT_SOURCE_SLOT_OR_PERIOD_CHANGED`

Interpretation:
- Exact same DataSource + current non-EOS period: alternate bytes reached the active Exo source path; investigate extractor/decoder/output next.
- Different DataSource: likely prefetch/stale generation or wrong source binding; fix selection binding only.
- Unresolved/no route: repair the identity link, not codecs or assets.

## CI checkpoint — BETA29 export run is active

- Renderer observer JVM run `46060063393`, run number 256 — SUCCESS. `NativeRendererStreamEvidenceTest`, `NativeExoAlternateByteRouteTest`, and `NativeRamilTrackOnlyLineageTest` passed, including NAV50 same-source/current-period and mismatch assertions.
- Owner preflight run `46060063423` — SUCCESS:
  - `jvm-issuer-proxy-contract` job `140711877640` — SUCCESS.
  - ARM13 native main 75s gate — SUCCESS, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
  - Persistent owner signer verified; install mode is update-existing.
  - `stage_a=NO_GO`, `audio_or_account_tested=false`, `stage_b_current_player_album_edition_attested=false`. This is a native stability/signing gate, not audio/product proof.
- Clone-alone run `46060063402` — SUCCESS, verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`; `audio_or_account_tested=false` and `stage_b_current_player_album_edition_attested=false`. Stability gate only.
- BETA29 diagnostic export run `46061697450`, run number 500, attempt 1, source `1afa88c78b5b3a3063fac5176f1152a95dcdf962` — IN_PROGRESS at last checkpoint. It is the only intended BETA29 export candidate: marker, README, artifact name and workflow expectations all say BETA29.

Several intermediate export-trigger commits were made while changing the artifact name. They may create older-name private drafts. Do not deliver or reference any draft from those intermediate runs. Only use run `46061697450` if it completes SUCCESS and its draft contains exactly `CELIKOM-A1-RAMIL-AU-BETA29-HONOR50-20261127.apk`.

Do not create any more `[export-beta-audio]` commits; run 500 is already active.

## Next action after run 500

1. Wait for run `46061697450` and all its jobs to complete. Confirm the ARM13 75s gate, persistent owner signer, update-existing mode, and BETA29 artifact checks.
2. Read the actual unpublished draft release ID from the completed run/logs or the exact tag created by that run. Verify the release contains the BETA29 APK, `BUILD-PROVENANCE.json`, `SHA256SUMS.txt`, and BETA29 `README-RU.txt`.
3. Update the trusted-main request `.github/deploy/a1-owner-download-request.json` with `run_id=46061697450`, `attempt=1`, and that exact draft `release_id`. This push triggers `.github/workflows/android-a1-owner-floki-spool.yml`.
4. Wait for independent root receipt and live `celikom.com` HTTPS verification. Confirm HTTP 200, APK content type, exact size and SHA-256, and unpublished draft readback.
5. Read the actual `A1_OWNER_DOWNLOAD_URL` from the draft. Send only that verified direct HTTPS URL from `celikom.com`. Never send a GitHub APK link, fabricate a URL, publish the draft, or bypass root verification.
6. The owner installs BETA29 over BETA28 without uninstalling or clearing data, reproduces the same tests and exports a fresh TXT.

The BETA29 phone test remains narrow:
- Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
- The second song that previously had leading gaps.
- Export TXT after both tests.

## Guardrails

- No second player.
- No audio transcoding or codec changes without evidence.
- No changes to server, catalogue, signed-grant authorization, Windows, stable Android or OTA.
- Do not infer audible replacement from `AUDIO_READ` alone or from CI.
- Do not ask the owner to resend BETA28 diagnostics or details already in this handoff.
