# CELIKOM Android A1 — BETA33 NAV53 first-open DataSource pin

Date: 2026-11-28  
Repository: manufact-test/nomusic  
Branch: experiment/android-a1-metrica-init-state-observer-arm13-20261112

**Current status:** BETA33 source built, signed and passed the trusted Floki/root delivery process. Owner phone test is still pending. Audible replacement is not proven.

## 1. BETA32 phone result

The owner installed BETA32 and reported that selecting Ramil / 10AGE — «Ау» produced the Yandex error «Невозможно воспроизвести трек» and skipped to the next track.

Diagnostic: CELIKOM-A1-Diagnostics-1795857597038.txt.

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

Counters are process-wide and do not attribute every event to «Ау». The direct listening report confirms that BETA32 failed to start the selected track. Positive DataSource reads do not prove that the bytes reached the active renderer or became audible.

## 2. BETA32 codec regression rollback

BETA32 repeated the request-only MP3 preference already tried in BETA25 and rolled back in BETA26. BETA32 changed the original FileInfo codecs query to mp3, but the phone TXT showed no MPEG decoder configuration and the owner reported that Yandex refused to play «Ау».

BETA33 restores original publisher codec negotiation:
- NativeIssuerCodecPreference is fail-closed and always returns false.
- Original FileInfo request arguments remain unchanged.
- The regression test verifies that the allowlisted target request, AAC request, owner-off request, unrelated track and non-original API all remain unchanged.
- ISSUER_CODEC_MP3_REQUESTED must remain NONE.

**Do not try the same query-only MP3 override again.** It did not establish that the original decoder selected MPEG and it caused a playback regression on BETA32.

## 3. Concrete source-link bug

In StageBAudioEvidence, onExoSourceInstanceCreated() recorded each exact factory product in ExactFactorySourceBirth, but then unconditionally replaced link.sourceInstance with the newly created product and reset the link's open/read state.

A later sibling/prefetch DataSource from the same Factory could therefore replace the exact DataSource selected at first open. The live renderer lookup could resolve the later object, while NativeExoAlternateByteRoute was armed against the earlier first-open object. This was consistent with the BETA32 evidence:
- many factory/DataSource products;
- one accepted deferred arm and one distinct positive linked read;
- current-period source lookup resolving;
- no route for the source returned by the live lookup.

The diagnostic did not prove this was the only runtime cause. It justified fixing the unconditional overwrite before exploring another boundary.

## 4. NAV53 code correction

NativeTrackSourceLink now has a firstOpenSourceCommitted flag.

- The exact first-open candidate is validated against the source birth, Factory, Descriptor, wrapper, creator Track and owner-approved beta token.
- The source is held as pending while deferred arm is in flight.
- The pin becomes committed only when armDeferredOriginalDataSource returns true for that exact DataSource.
- Later DataSource products are still recorded as exact factory births, but cannot replace a pending/committed source or reset its open/read state.
- A rejected arm clears the pending pin.
- An exact Descriptor rebuild clears pending and committed state for a new lineage.
- If the committed weak source has been collected, the pin is cleared and normal fail-closed candidate handling resumes.

No second player, source URL inference, track-name matching, broader allowlist, server/catalog change, authorization change, Windows change, stable Android change or OTA change.

## 5. Regression test and CI history

NativeRamilTrackOnlyLineageTest covers:
1. Exact owner-approved wrapper/descriptor/factory/DataSource lineage.
2. First-open source held pending during deferred arm.
3. Sibling creation while arm is pending cannot replace the selected source.
4. Successful arm promotes the exact source to committed.
5. Later sibling creation cannot replace the committed source.
6. Rejected arm does not pin an unarmed source.
7. Descriptor rebind clears the old pin and permits a new exact lineage.
8. Existing weak descriptor/factory lifetime, wrong-track, wrong-issuer and unrelated-wrapper checks remain.

Initial workflows on commit e2823bacaa96440674c6063883854d8600f5b540 failed:
- owner/export run 46131587104 — failure at NAV53_FIRST_OPEN_SOURCE_PIN_SURVIVES_LATER_FACTORY_PRODUCT;
- JVM run 46131587051 — same NAV53 regression assertion failed.

Follow-up commit 6972ee7fbee06be8eec90be51f886deb48ef265b normalized a whitespace-sensitive source assertion in test_a1_stage_b_audio_evidence.py. The production implementation was not changed by that follow-up. The later full reruns passed:
- owner build/export run 46132374238 — SUCCESS;
- JVM run 46132374233 — SUCCESS;
- clone-alone ARM13 run 46132374224 — SUCCESS.

The first Java assertion failure was not independently explained by a production-code change; it did not reproduce on the later run. Keep this history visible rather than describing the first failure as conclusively fixed by a source change.

Native verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO. The report states audio_or_account_tested=false, stage_a=NO_GO, stage_b_current_player_album_edition_attested=false and acoustic_replacement_proven=false.

## 6. Signed BETA33 APK and trusted delivery

Source commit used for the successful owner build: 6972ee7fbee06be8eec90be51f886deb48ef265b.

- Owner build/export run: 46132374238, attempt 1 — SUCCESS.
- JVM run: 46132374233 — SUCCESS.
- Clone-alone ARM13 run: 46132374224 — SUCCESS.
- APK: CELIKOM-A1-RAMIL-AU-BETA33-HONOR50-20261128.apk.
- Size: 71,602,156 bytes.
- SHA-256: 41e0abea857cd6159edf20e38b25e9e594621fdda86da68bc0471aadc839fd61.
- Persistent owner signer SHA-256: 048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf.
- Private unpublished owner draft release ID: 461461193.

Trusted Floki delivery:
- Floki spool run 46133753704, run 41 — SUCCESS.
- Root receipt and unpublished owner draft readback passed.
- Final marker: A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED.
- Root receipt recorded https_verified=true.
- The actual owner capability URL is stored only in the unpublished private draft. It is intentionally omitted from Git, docs, logs and public messages.

The APK and trusted delivery pipeline are complete. This record does not confirm that the owner capability URL was actually sent to or received by the owner. If the owner does not have the link, retrieve the real value from the unpublished draft and send it privately. Do not rebuild or repeat Floki delivery for this APK.

## 7. Owner acceptance — pending

After the owner has the verified direct link:

1. Install BETA33 over BETA32 on the existing Honor 50. Do not uninstall CELIKOM or clear app data/cache.
2. Confirm CELIKOM is ВКЛ.
3. Test Ramil / 10AGE — «Ау», album 38902809, track 144530503, segment 00:43–00:54. First report whether Yandex starts the original track without its error.
4. Test the second song that previously had leading gaps.
5. Export a fresh BETA33 TXT using the normal short-press action.
6. Separately report whether alternate audio was actually heard inside the original Yandex Music app.

CI success, DataSource reads and current-period counters are not proof of audible replacement. Use the phone result and current-period source evidence to choose the next functional correction. Do not repeat authorization, grant or audio-download investigations, and do not add broad telemetry-only work.
