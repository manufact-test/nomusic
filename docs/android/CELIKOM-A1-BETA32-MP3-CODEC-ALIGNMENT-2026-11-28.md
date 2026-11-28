# CELIKOM Android A1 — BETA32 MP3 codec alignment

Date: 2026-11-28  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Purpose

BETA32 addresses the concrete format-negotiation mismatch found in the fresh BETA31 NAV52 phone diagnostic. It does not claim that audible replacement has been proven.

## BETA31 evidence used for the correction

The BETA31 TXT showed:

- The approved signed alternate source was available as `audio/mpeg`.
- The exact alternate DataSource was armed, opened and returned positive reads.
- The original FileInfo codec request had `ISSUER_CODEC_MP3_REQUESTED=NONE`.
- Codec evidence showed `CODEC_CONFIG_AAC=FEW` and `CODEC_CONFIG_MPEG=NONE`.
- The renderer witness showed `ENGINE_HOLDER_RENDERER_TYPE1=MANY`, `ENGINE_HOLDER_TYPE1_STATE_NOT2=MANY` and `ENGINE_HOLDER_READ_RETURN_MINUS3=MANY`; no confirmed state-2/`-4` current-period audio read was established.
- Current-period alternate-source correlation remained absent.

This is a concrete mismatch between the approved MPEG source and the original Yandex FileInfo codec preference. It is not proof that this was the only playback failure.

## Code correction

Production file:

`android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/NativeIssuerCodecPreference.java`

BETA32 restores MP3 preference under strict guards:

1. CELIKOM owner mode is enabled.
2. The caller has identified the exact original Yandex FileInfoApi.
3. The method has one unique String `@Query("trackId")` parameter, matching the inspected track index.
4. The value is one of the three explicit `NativeTrackIdBetaPolicy` trial track IDs.
5. The method has one unique String `@Query("codecs")` parameter.
6. Only the codecs argument is set to `mp3`.

Other request arguments are untouched. Owner-off, non-allowlisted tracks, other API methods, missing or ambiguous query annotations, mismatched argument counts and non-String parameters fail closed. No global codec rewrite, second player, new playback clock or server change was introduced.

## Focused regression

Test:

`android/native-yandex-hooklab/tests/src/pro/celikom/a1exitwitness/NativeIssuerCodecPreferenceTest.java`

Result marker: `BETA32_ALLOWLISTED_MP3_CODEC_PREFERENCE_PASS`.

Coverage includes all three allowlisted IDs; AAC and mixed codec inputs; already-MP3 input; owner-off; non-allowlisted track; non-original API; wrong track index; argument-count mismatch; ambiguous/missing codecs query; non-String codecs and non-String track ID.

Existing native lifecycle, grant and source-target gates also passed, including:
- `NativePrePrepareAdmission`: 35,039 assertions.
- `NativeReplacementLifecycle`: 30,086 assertions.
- `NativeGrantContract`: 50 safety assertions.
- NAV28 publisher-signed exact queue-slot target.
- NAV31 publisher-signed period-to-child-stream adapter fields.
- NAV41 pinned signed player current-period target.
- NAV45 exact MediaItem unique final logical string gate.
- Private original child-source target.

## Build and signed artifact

- Source commit: `8289597ab83a5ea93cc93ee5ab33b634f2d683e9`.
- Source/export workflow run: `46127527304`, attempt 1 — SUCCESS.
- Native verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- The original publisher installed and launched; publisher-first/clone-second 75-second native stability test passed.
- The native test explicitly reports `audio_or_account_tested=false`, `stage_b_current_player_album_edition_attested=false`, `stage_a=NO_GO`, and no same-object MediaDataSource extractor read. It does not prove audible replacement.
- APK: `CELIKOM-A1-RAMIL-AU-BETA32-HONOR50-20261128.apk`.
- Size: 71,606,252 bytes.
- SHA-256: `8b09bcf74b526263aa1a36de356b9207a806f822cad2338c818ef9a5697518ad`.
- Persistent owner signer verified. The APK signer SHA-256 matches the installed original application certificate: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
- Unpublished owner draft release ID: `461427239`.

## Trusted Floki delivery

- Main request JSON points to source run `46127527304`, attempt 1, draft release `461427239`.
- Initial Floki run `46128588358` was accepted by `celikom-floki-ci01` but remained step-less. The exact no-step recovery workflow issued cancel/force-cancel requests.
- The retry Floki run `46128754869`, attempt 1, job `140929898949`, ran on `celikom-floki-ci02` — SUCCESS.
- Exact source run, provenance, package, persistent signer, file size and SHA-256 were verified before staging.
- Root receipt `a1-46127527304-1.json` was independently verified with `https_verified=true`.
- The unpublished owner draft was patched and read back with exactly one matching celikom.com capability URL. The direct URL was delivered privately to the owner and is deliberately omitted from Git/docs/logs.

No runner restart, permission change, server change, security relaxation or delivery bypass was used. The Android APK was not rebuilt for the Floki retry.

## Owner acceptance — still pending

Install BETA32 over BETA31 on the existing Honor 50. Do not uninstall CELIKOM or clear data/cache. Confirm CELIKOM is `ВКЛ`.

Test Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`, then the second song that previously had leading gaps. Export a fresh BETA32 TXT and report whether the alternate audio was actually heard inside original Yandex Music.

The next diagnostic must verify the MP3 request/codec counters and whether the same alternate source reaches the current playback period and renderer. Positive DataSource reads alone do not prove audio output.

**Do not mark BETA32 as a working replacement until the owner confirms audible alternate audio.**
