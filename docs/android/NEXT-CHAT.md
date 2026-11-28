# CURRENT HANDOFF — BETA33 NAV53 source pin; build/export pending

Date: 2026-11-28  
Repository: manufact-test/nomusic  
Working branch: experiment/android-a1-metrica-init-state-observer-arm13-20261112

## Read first

1. docs/android/NEXT-CHAT.md
2. docs/android/CELIKOM-A1-BETA33-NAV53-FIRST-OPEN-SOURCE-PIN-2026-11-28.md
3. docs/android/CELIKOM-A1-BETA32-MP3-CODEC-ALIGNMENT-2026-11-28.md
4. docs/android/CELIKOM-A1-BETA31-NAV52-COMMITTED-CURSOR-LIFETIME-2026-11-28.md
5. docs/android/CELIKOM-A1-BETA30-NAV51-LIVE-DATASOURCE-WITNESS-2026-11-27.md
6. docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md

## BETA32 owner result

The owner installed BETA32 and reported that selecting Ramil / 10AGE — «Ау» now produces the Yandex error «Невозможно воспроизвести трек» and skips to the next track. The fresh file was CELIKOM-A1-Diagnostics-1795857597038.txt.

Important counters from that file:
- ISSUER_CODEC_MP3_REQUESTED = FEW.
- CODEC_CONFIG_MPEG = NONE; CODEC_CONFIG_AAC = FEW.
- DATASOURCE_ARMED / AUDIO_OPEN / AUDIO_READ were positive.
- FIRST_OPEN_CANDIDATE_ACCEPTED = FEW; FIRST_OPEN_DEFERRED_ARM_ACCEPTED = ONE.
- TRACK_SOURCE_DISTINCT_POSITIVE_READ = ONE; EXO_SOURCE_INSTANCE = MANY.
- LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT = MANY.
- LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH = MANY; LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED = MANY.
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS = NONE.
- LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD = MANY.
- LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD = MANY.

The renderer counters are process-wide; do not claim they identify a particular song or prove audible output. The user's direct listening report is the evidence that «Ау» fails to start on BETA32.

## BETA33 correction

BETA32 repeated the old request-only MP3 override that had already been rolled back after BETA25/BETA26. The phone TXT showed that the request was changed but no MPEG decoder configuration was observed, and the owner reported a playback regression. BETA33 restores original Yandex codec negotiation; it does not force MP3.

A second concrete source-identity bug was found in StageBAudioEvidence:
- onExoSourceInstanceCreated() recorded every factory product but also unconditionally replaced the wrapper's sourceInstance.
- A later sibling/prefetch DataSource could therefore replace the exact DataSource accepted at first open.
- The live renderer lookup could then resolve a source that had no matching armed route, consistent with the BETA32 NO_ROUTE / no same-current-period evidence.

NAV53 adds a pending/committed first-open source pin:
- The exact source is protected as pending while its deferred arm is in flight.
- It becomes committed only when armDeferredOriginalDataSource returns true for that exact DataSource.
- Later products from the same factory are still recorded as births, but cannot overwrite a pending/committed source or reset its open/read state.
- A rejected arm clears the pending pin; the exact descriptor rebuild clears both pending and committed state for a new lineage.
- The existing fail-closed creator, track, factory, descriptor, generation and grant checks remain.

The JVM regression creates a later sibling DataSource after the first source has opened/read and verifies that the live source remains the exact first-open DataSource, the sibling cannot replace/re-arm it, and a descriptor rebind allows a new source.

## BETA33 build and delivery

- Source commit: pending.
- Source/export workflow: pending.
- Private owner draft and trusted Floki/root delivery: pending.
- APK must be named CELIKOM-A1-RAMIL-AU-BETA33-HONOR50-20261128.apk.
- Do not send a GitHub release URL. Send the direct owner capability URL only after the trusted Floki/root receipt and live HTTPS size/hash verification succeed.
- Keep the owner draft unpublished and never write its capability URL/token into Git, docs, logs or public messages.

## Owner acceptance

After verified delivery:
1. Install BETA33 over BETA32 on the existing Honor 50. Do not uninstall CELIKOM or clear app data/cache.
2. Confirm CELIKOM is ВКЛ.
3. Test «Ау», album 38902809, track 144530503, segment 00:43–00:54. First report whether Yandex now starts the original track without its error.
4. Test the second song that previously had leading gaps.
5. Export a fresh BETA33 TXT with the normal short-press action.
6. Report separately whether the alternate audio was actually heard inside the original Yandex Music app.

Do not repeat authorization, grant or audio-download investigations. Do not add broad telemetry-only work. Use the phone result and current-period source evidence to choose the next functional correction.

## Boundaries and priority

The goal is audible replacement inside the original Yandex Music app as quickly as possible. Diagnostics and CI are gates to a working phone build, not milestones. Keep Android application changes on the experiment branch. Do not merge to main without successful phone acceptance and explicit owner approval. Do not change server/catalog, signed grants, Windows, stable Android or OTA without a separate justified need and authorization. Keep the original Yandex player; no second player or new architecture shortcut. Never claim audible success from CI or byte-read counts.
