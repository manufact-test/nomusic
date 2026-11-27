> **Superseded build note — BETA28 (27.11.2026):** BETA28 retains the exact descriptor first-open lifetime fix unchanged and adds owner-session recovery. Source commit `895306cee0934e245aeda7aaa0ce95f3b609eff2`; APK size 71,602,156 bytes; SHA-256 `2c5dee053f2634224f929113e94b5aafe5ca5492160ed16f8e267020b394555c`. Source/JVM/ARM13 checks passed. BETA28 delivery is pending Floki spool run `46052141389`; BETA27 remains latest delivered. See the BETA28 handoff for exact status and owner test instructions.

> **Delivery update (27.11.2026):** Trusted Floki spool workflow `46048173341` completed SUCCESS. Independent root-owned HTTPS receipt, live byte-count/SHA verification and unpublished owner draft readback passed. The direct `celikom.com` URL was sent privately; it is deliberately not copied into Git, docs or logs. BETA27 is delivered; owner audio test is still pending.

# CELIKOM Android A1 — BETA27 exact descriptor first-open lifetime

Date: 27.11.2026  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Android source commit: `2b755397b577202de5879b81a71b1a51cce5e711`  
Owner workflow: `46028046471` (SUCCESS)  
Clone-alone differential: `46028046465` (SUCCESS)

## Why BETA27 exists

BETA26 restored normal playback of Ramil / 10AGE — «Ау» after disabling the request-only MP3 rewrite. The owner reported that «Ау» plays again, but no CELIKOM replacement is audible.

The BETA26 diagnostic contained:
- `ISSUER_CODEC_MP3_REQUESTED=NONE`
- approved owner resolve / signed audio / range evidence
- exact descriptor → factory → DataSource source-lineage evidence
- `FIRST_OPEN_DESCRIPTOR_LOST=ONE`
- no successful CELIKOM `DATASOURCE_ARMED`, `AUDIO_OPEN`, or `AUDIO_READ` evidence.

The observed first-open candidate rejection led to a narrow source-lifetime hypothesis: `NativeTrackSourceLink.descriptor` was weakly held and could be collected after the exact descriptor/factory handoff but before the corresponding DataSource's first OPEN.

## Exact code change

In `StageBAudioEvidence.NativeTrackSourceLink`:
- Added a strong `firstOpenDescriptorPin` field.
- Set it only after `findByDescriptor(descriptor)` has established exact Java identity for the descriptor→factory handoff.
- Keep it within the existing bounded lineage table; it is not an alternate admission token.
- Release it when the exact source or its sibling is touched, when descriptor is rebound, or if source lineage is already touched / saturated.
- No Track/Album, creator, setter, generation, permission, fresh-source or fail-closed check was relaxed.
- Original Yandex codec request remains unchanged; no server, catalogue, signed permission, Range/HMAC, Windows, stable Android or OTA change.

A deterministic JVM regression test checks retention across unrelated candidate inspection, rejection of an unrelated source, release on first source touch and sibling close, and release/rejection after descriptor rebind.

## CI results and limits

Owner workflow `46028046471` completed SUCCESS:
- JVM issuer/proxy contract and new Stage B descriptor-lifetime regression passed.
- Original codec passthrough test passed.
- Exact Exo factory product identity bridge test passed.
- Fresh Android 13 ARM64/ARMv7 publisher-first/clone-second test passed.
- Original publisher remained stable for 75 seconds before clone; both apps remained concurrently installed.
- Native clone main accepted for 75 seconds.
- Persistent owner signer matched the installed certificate.

Exact verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.

The same run report explicitly records:
- `stage_a=NO_GO`
- `audio_or_account_tested=false`
- `stage_b_current_player_album_edition_attested=false`
- no MediaDataSource readAt candidates
- `acoustic_replacement_proven=false`.

Therefore CI success means the native launch / install and scoped module checks passed. It does NOT prove that the correct current player track was intercepted, that CELIKOM DataSource was armed/read, or that alternate audio was audible.

## APK and delivery

Expected owner APK:
- Filename: `CELIKOM-A1-RAMIL-AU-BETA27-HONOR50-20261127.apk`
- Size: `71,598,060` bytes
- SHA-256: `5939d5f9c8dc7661c5eac64f06391bf06f854b1da79158dfacc2f41f74f918c1`
- Persistent signer SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`
- Draft release ID: `460809106`, unpublished.

Trusted main request JSON points to source workflow `46028046471`, attempt 1, release `460809106`. Floki spool workflow `46048173341` verified source provenance, artifact digest and package signer and staged the APK. At the time this document was written it was waiting for the independent root-owned HTTPS receipt. **No owner celikom.com URL is confirmed here.** Never use a GitHub download URL or fabricate the celikom.com capability URL.

Finish the existing Floki root receipt, live HTTPS 200/content-type/byte-count/SHA-256 verification, unpublished draft update and readback. Only then send the direct celikom.com link privately.

## Owner test after verified delivery

Install over BETA26 without uninstalling CELIKOM or clearing data. In original Yandex Music:
1. Play Ramil / 10AGE — «Ау», album `38902809`, original track `144530503`, listen around `00:43–00:54`.
2. Play the second song that previously had leading gaps.
3. Export one fresh CELIKOM diagnostic after both tests; avoid restarting Yandex between tests if possible.

Inspect the full chain:
`FIRST_OPEN_HOOK_ENTERED` → `FIRST_OPEN_CANDIDATE_ACCEPTED` → `FIRST_OPEN_SETTER_MATCH` → `FIRST_OPEN_DEFERRED_ARM_CALLED` → `DEFERRED_ARM_ENTER` → `DEFERRED_ARM_ACCEPTED` → `DATASOURCE_ARMED` → `AUDIO_OPEN` → `AUDIO_READ`.

Separate events by actual Track and selection generation. Do not infer the result from aggregate counters alone. Require owner listening confirmation for real replacement.

## Required continuation reading

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md`
3. This file
