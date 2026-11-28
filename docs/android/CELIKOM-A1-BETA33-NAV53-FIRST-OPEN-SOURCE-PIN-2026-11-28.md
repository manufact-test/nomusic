# CELIKOM Android A1 — BETA33 NAV53 first-open DataSource pin

Date: 2026-11-28  
Repository: manufact-test/nomusic  
Branch: experiment/android-a1-metrica-init-state-observer-arm13-20261112

## 1. BETA32 phone result

The owner installed BETA32 and reported that selecting Ramil / 10AGE — «Ау» produced the Yandex error «Невозможно воспроизвести трек» and skipped to the next track.

Fresh diagnostic: CELIKOM-A1-Diagnostics-1795857597038.txt.

Relevant evidence:
- ISSUER_CODEC_MP3_REQUESTED = FEW.
- CODEC_CONFIG_MPEG = NONE; CODEC_CONFIG_AAC = FEW.
- DATASOURCE_ARMED / AUDIO_OPEN / AUDIO_READ were positive.
- FIRST_OPEN_CANDIDATE_ACCEPTED = FEW; FIRST_OPEN_DEFERRED_ARM_ACCEPTED = ONE.
- TRACK_SOURCE_DISTINCT_POSITIVE_READ = ONE; EXO_SOURCE_INSTANCE = MANY.
- LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT = MANY.
- LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH = MANY.
- LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED = MANY.
- LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS = NONE.
- LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD = MANY.
- LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD = MANY.

These counters are process-wide and do not attribute every event to «Ау». The listening result is direct owner evidence; the counters locate the unresolved source/renderer boundary but do not prove sound.

## 2. BETA32 codec regression rollback

BETA32 repeated the request-only MP3 preference that had already been disabled after the BETA25 experiment and BETA26 phone result. BETA32 changed the original FileInfo codecs query to mp3, but the fresh TXT did not show an MPEG decoder configuration and the owner reported that Yandex refused to play «Ау».

BETA33 restores original publisher codec negotiation:
- NativeIssuerCodecPreference is fail-closed and always returns false.
- Original FileInfo request arguments remain unchanged.
- The regression test verifies that the allowlisted target request, AAC request, owner-off request, unrelated track and non-original API all remain unchanged.
- ISSUER_CODEC_MP3_REQUESTED should remain NONE.

Do not try the same query-only MP3 override again. It did not establish that the original decoder selected MPEG.

## 3. Concrete source-link bug

In StageBAudioEvidence, onExoSourceInstanceCreated() correctly recorded each exact factory product in ExactFactorySourceBirth, but then unconditionally replaced link.sourceInstance with the newly created product and reset the link's open/read state.

The exact first-open source could therefore be replaced by a later sibling/prefetch DataSource from the same factory. The live renderer lookup would then resolve the later object, while NativeExoAlternateByteRoute was armed against the earlier first-open object. This is a concrete code path consistent with:
- many factory/DataSource products;
- one accepted deferred arm and one distinct positive linked read;
- current-period source lookup resolving;
- no route for the source returned by the live lookup.

The diagnostic does not prove this was the only runtime cause. It does justify fixing the unconditional overwrite before exploring another boundary.

## 4. NAV53 code correction

NativeTrackSourceLink now has a firstOpenSourceCommitted flag.

- exactFreshCreatorOrBetaAtFirstOpen() validates the exact source birth, factory, descriptor, wrapper, creator Track and owner-approved beta token, then holds that source as pending while the deferred arm runs.
- The pin becomes committed only when armDeferredOriginalDataSource returns true for that exact DataSource.
- Later DataSource products are still recorded as exact factory births and cannot replace a pending/committed source or reset its open/read state.
- A rejected arm clears the pending pin. The exact descriptor rebuild clears both pending and committed state for a new source lineage.
- If the committed weak source has been collected, the pin is cleared and normal fail-closed candidate handling resumes.

No new player, source URL inference, track-name matching, broader allowlist, server/catalog change, authorization change, Windows change, stable Android change or OTA change.

## 5. Regression test

NativeRamilTrackOnlyLineageTest now:
1. Creates the exact owner-approved wrapper/descriptor/factory/DataSource lineage.
2. Selects the exact first-open source and holds it pending during the deferred arm.
3. Creates a sibling while the arm is pending and verifies it cannot replace the selected source.
4. Promotes the pin after a successful arm, then opens and reads the exact source.
5. Creates a later sibling DataSource and verifies the live resolver still returns the committed source.
6. Verifies the sibling cannot replace or re-arm the committed source.
7. Verifies a rejected arm does not pin an unarmed source.
8. Verifies descriptor rebind clears the old pin and permits a new exact factory/DataSource lineage.
9. Retains the existing weak descriptor/factory lifetime, wrong-track, wrong-issuer and unrelated-wrapper checks.

The original NativeExoAlternateByteRouteTest, native JVM gates and publisher-first Android 13 ARM64/ARMv7 gates remain required.

## 6. BETA33 artifact and owner acceptance

Build/export and delivery are pending until the workflow completes.

Expected owner artifact: CELIKOM-A1-RAMIL-AU-BETA33-HONOR50-20261128.apk.

After trusted Floki/root delivery:
- Install over BETA32 without uninstalling CELIKOM or clearing app data/cache.
- Confirm CELIKOM is ВКЛ.
- Test «Ау» track 144530503 at 00:43–00:54 and report whether Yandex starts the track without error.
- Test the second song with prior leading gaps.
- Export fresh BETA33 TXT.
- Separately report whether alternate audio was actually heard.

CI success, DataSource reads and current-period counters are not proof of audible replacement. Keep source on the experiment branch; main/stable/OTA remain untouched.
