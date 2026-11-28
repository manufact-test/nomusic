# CURRENT HANDOFF — BETA32 delivered; phone audio test pending

Date: 2026-11-28  
Repository: `manufact-test/nomusic`  
Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Read first

1. `docs/android/NEXT-CHAT.md` — this current handoff.
2. `docs/android/CELIKOM-A1-BETA32-MP3-CODEC-ALIGNMENT-2026-11-28.md` — BETA31 evidence, BETA32 code correction, tests, build and verified delivery.
3. `docs/android/CELIKOM-A1-BETA31-NAV52-COMMITTED-CURSOR-LIFETIME-2026-11-28.md` — exact cursor lifetime correction.
4. `docs/android/CELIKOM-A1-BETA30-NAV51-LIVE-DATASOURCE-WITNESS-2026-11-27.md` — DataSource identity lineage and NAV51 evidence.
5. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md` — trusted delivery history and security boundary.

## Current state

- **BETA32 is built, signed and delivered through the root-verified celikom.com route.**
- Android source commit: `8289597ab83a5ea93cc93ee5ab33b634f2d683e9`.
- Source/export workflow run `46127527304`, attempt 1 — SUCCESS.
- Owner JVM codec regression and existing native gates — SUCCESS.
- Fresh Android 13 ARM64/ARMv7 native verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. The app launch/stability test passed; audio/account playback was not tested. This is **not** proof of audible replacement.
- APK: `CELIKOM-A1-RAMIL-AU-BETA32-HONOR50-20261128.apk`, 71,606,252 bytes.
- SHA-256: `8b09bcf74b526263aa1a36de356b9207a806f822cad2338c818ef9a5697518ad`.
- Persistent owner signer verified; installed original certificate SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
- Unpublished owner draft release ID: `461427239`.
- Trusted Floki delivery run `46128754869`, attempt 1, job `140929898949`, runner `celikom-floki-ci02` — SUCCESS.
- Root receipt `a1-46127527304-1.json` recorded `https_verified=true`; exact source run, provenance, signer, package, size and SHA were checked. The unpublished owner draft was patched and read back with the exact capability URL.
- The owner capability URL was delivered privately in this conversation. Never copy it into Git, documentation, Actions logs or public summaries.
- **Owner installation, listening result and fresh BETA32 diagnostic TXT are pending. Audible replacement is not yet proven.**

## Why BETA32 was necessary

The fresh BETA31 TXT showed that the signed alternate source was obtained and the exact native DataSource was armed, opened and returned positive bytes. However, the original FileInfo codec negotiation still showed `ISSUER_CODEC_MP3_REQUESTED=NONE`, `CODEC_CONFIG_AAC=FEW`, `CODEC_CONFIG_MPEG=NONE`. The renderer witness also showed type-1 renderer reads while state was not STARTED and `-3` (NOTHING_READ), without confirmed state-2/`-4` or current-period alternate-source correlation.

The concrete mismatch was that CELIKOM's approved source is `audio/mpeg` while the original Yandex FileInfo request was still using its previous AAC codec preference.

BETA32 changes only the original FileInfo `codecs` query, and only when all guards match: owner mode enabled, exact original FileInfoApi, the annotated publisher `trackId` is one of the three explicit trial IDs, and one unambiguous String `@Query("codecs")` exists. Only that argument becomes `mp3`. Other tracks, owner-off, other APIs and ambiguous signatures remain unchanged. No second player was added.

## Next task — real phone acceptance

The owner will provide the fresh BETA32 diagnostic TXT in the next chat. It has not been received yet. Do not ask for a re-export or start unrelated investigation before reviewing that file; once it arrives, inspect it together with the listening result and move directly to the smallest justified functional correction.


The owner should now:

1. Install BETA32 **over BETA31** on the existing Honor 50. Do not uninstall CELIKOM or clear app data/cache.
2. Confirm CELIKOM status is `ВКЛ`.
3. Play Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, and listen to `00:43–00:54`.
4. Test the second song that previously had leading gaps.
5. Export a fresh BETA32 TXT using the normal short-press diagnostic action.
6. Report separately whether the alternate audio was actually heard inside the original Yandex Music app.

In the fresh TXT, check whether `ISSUER_CODEC_MP3_REQUESTED` and `CODEC_CONFIG_MPEG` become positive for the allowlisted track, and whether `DATASOURCE_ARMED` / `AUDIO_OPEN` / `AUDIO_READ` remain positive. The key downstream witness is `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS`. Even that counter alone is not proof of audible output.

If MP3 negotiation and source reads are positive but the owner still hears no replacement, do not repeat authorization, grant or DataSource-download investigations. Use the new renderer/current-period evidence to repair the actual active renderer/decoder handoff. Do not create another broad telemetry-only round unless a specific missing fact is required to choose the fix.

## Overriding development priority — speed to audible mobile success

The goal is a working Android replacement inside the original Yandex Music app as quickly as possible. Diagnostics, source inspection and CI are tools, not milestones. Read the fresh TXT, identify the most direct justified correction, implement it, run the necessary gates and deliver the next testable build. Avoid speculative detours, repetitive investigations and unnecessary status reports. Measure progress by actual audible playback and time to the next meaningful correction, not by the number of completed checks.

## Delivery recovery reference

BETA32's first Floki push landed on CI01 with an in-progress job and zero workflow steps. The existing exact no-step recovery workflow issued cancel/force-cancel requests. A second trusted delivery run was accepted by CI02 and completed successfully. No runner restart, permission change, security relaxation, delivery bypass or APK rebuild was required for the retry. See the Floki delivery document for the historical runner evidence.

## Boundaries

Keep Android application changes on the working branch. Do not merge to `main` without a successful phone result and explicit owner approval. Do not change server/catalog, signed grants, Windows, stable Android or OTA without a separate justified need and authorization. Keep the original Yandex player; no second player or new architecture as a shortcut. Do not ask the owner to operate GitHub Actions. Final success means the owner hears the intended alternate audio inside original Yandex Music, not CI SUCCESS or byte-read counts.
