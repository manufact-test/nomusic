# CELIKOM A1 BETA26 — owner diagnostic next steps

Date: 2026-11-27  
Device: HONOR 50 / Android 13  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Current state

BETA26 has been built and delivered through the verified Floki spool. Its direct HTTPS download link from `celikom.com` was sent privately to the owner.

- Source commit: `bcb5d9ccee56b2e8bcc5493c12514c07f342ee6b`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA26-HONOR50-20261127.apk`.
- Size: `71,598,060` bytes.
- SHA-256: `43e5bb00eabde955eff8e2b25b76986a29198fa3f7ca0512cc55ff234b245888`.
- No fresh BETA26 phone TXT is included in this documentation. The next chat must inspect the diagnostic attached by the owner before changing code.

## What BETA26 changed

BETA25 had a request-only MP3 codec override that replaced the original Yandex FileInfoApi `codecs` argument with only `mp3`, even though the CELIKOM DataSource never reached `DATASOURCE_ARMED`, `AUDIO_OPEN`, or `AUDIO_READ`.

BETA26 disables that override. `NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo()` returns `false` and does not inspect or mutate the original arguments. Original Yandex codec negotiation should pass through unchanged.

Expected diagnostic: `ISSUER_CODEC_MP3_REQUESTED=NONE`.

This is a playback-safety rollback, not proof that the codec override was the only cause and not an audio-replacement fix.

## Owner test context

- Original Yandex Music application.
- Ramil / 10AGE — «Ау».
- Original album ID: `38902809`.
- Original track ID: `144530503`.
- Listen at `00:43–00:54`.
- Then play another track that previously had gaps at the beginning.
- Keep both checks in one Yandex session; do not restart between tracks.
- Record whether «Ау» plays normally or Yandex reports «Невозможно воспроизвести», whether the second song has leading gaps, and whether alternate CELIKOM audio is actually audible.

Do not uninstall CELIKOM or clear data/cache for this test.

## Diagnostic reading order

First confirm the diagnostic belongs to BETA26 and that `ISSUER_CODEC_MP3_REQUESTED=NONE`.

Then isolate the original Yandex playback failure for «Ау»:
- Find the exact track-scoped PlaybackException.
- Record exception class, message, error code and cause.
- Correlate it with the original track ID and selection generation.
- Do not attribute an original Yandex failure to the signed CELIKOM MP3 unless the CELIKOM source was actually opened/read.

Next find the first missing/rejected stage in the CELIKOM path:

`FIRST_OPEN_HOOK_ENTERED` → `FIRST_OPEN_CANDIDATE_ACCEPTED` → `FIRST_OPEN_SETTER_MATCH` → `FIRST_OPEN_DEFERRED_ARM_CALLED` → `DEFERRED_ARM_ENTER` → `DEFERRED_ARM_ACCEPTED` → `DATASOURCE_ARMED` → `AUDIO_OPEN` → `AUDIO_READ`.

Inspect rejection reasons and counts around:
- `FIRST_OPEN_SOURCE_ALREADY_TOUCHED`
- `FIRST_OPEN_BIRTH_NOT_FOUND`
- first-open candidate accepted/rejected reason
- exact setter match
- deferred arm enter/accepted/rejected
- source identity / wrapper / factory / generation mismatch.

Keep «Ау» and the second song separated by original track ID and generation. Do not combine events across the track transition.

## How to interpret the outcomes

- `ISSUER_CODEC_MP3_REQUESTED=NONE` and «Ау» plays: supports the codec-override hypothesis, but does not prove replacement.
- `ISSUER_CODEC_MP3_REQUESTED=NONE` and «Ау» still fails: investigate the original Yandex PlaybackException and codec pass-through path.
- Normal playback resumes but `DATASOURCE_ARMED` remains absent: continue on the exact first-open / deferred-arm handoff.
- `DATASOURCE_ARMED`, `AUDIO_OPEN`, and `AUDIO_READ` appear: verify they belong to the correct selected track/generation, then require owner listening confirmation.
- No CI/native-launch result alone is proof that alternate audio reached the user's speakers.

## Rules for the next implementation

- Inspect the attached TXT first and identify the first proven failing transition.
- Do not create another diagnostic-only APK if the existing TXT already exposes the rejection.
- Do not perform broad or speculative refactors.
- Do not change server, catalogue, signed permissions, Range/HMAC, Windows, stable Android, original Yandex APK, or OTA without direct evidence.
- Fix only the first demonstrated cause; run the narrow JVM and Android 13 regression gates.
- Do not build or deliver another APK until the diagnostic justifies a code change.
- If another APK is needed, use only the trusted Floki spool and send a verified direct `celikom.com` link. Never send a GitHub download link.

## Required reading

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md`
3. This file
