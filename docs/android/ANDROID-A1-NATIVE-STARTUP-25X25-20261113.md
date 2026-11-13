# CELIKOM Android A1 — native startup verification, 13 Nov 2026

## Confirmed tests

Android 13 ARM native CI, original Yandex installed first and CELIKOM alongside it:
- Standalone #43412506017 and paired #43412506076: CELIKOM 25/25, original 25/25 in paired test.
- Standalone #43413689898 and paired #43413689837: repeat 25/25 and direct runtime resource lookup verification.
- CELIKOM active resource location: OUTER_OWN. Both expected Firebase resource identifiers resolve in CELIKOM namespace (PAIR_BOTH); original namespace returns PAIR_NONE in clone.
- Controller: ENTER 1, RETURN 1, THROW 0.
- The original application remained installed and stable. No real account, audio or controls test was performed.

## Exact code and backups

Verified code: 0b8591329aae1e8b4c7f8f71815a12ee4dcc8e01.
Backup: backup/android-a1-firebase-namespace-success-witness-20261113.
Earlier successful backup: backup/android-a1-first-paired-25x25-resource-route-native-pass-20261113.
Earlier read-only negative/causal baseline: backup/android-a1-loadedapk-inner-cache-native-proof-20261113.

## Interpretation

The native MAIN startup blocker is resolved in disposable tests. This is **not** a consumer release: audio replacement, authorization, pause, seek, next and radio have not been accepted. The native resource-route experiment is opt-in in CI and disabled by default in other builds. Keep all existing project boundaries and do not change Test.50, original Yandex, Windows or production.

Next: review the existing B42 audio contract, identify the native source integration point, then test actual audio and controls before preparing a user APK. Do not repeat the closed startup and Firebase investigations.


## Next workstream — exact native audio bridge, not yet implemented

- The existing `android/native-audio-contract/source-contract.mjs` on the active branch is byte-identical to the tested B42 branch (Git blob `213f1c299ceacdb825cfe739ebb084e9073ff4ea`). No reimplementation or blind B42 merge is necessary. Source-level HTTP tests previously passed 45/45 (#43183941538).
- Current B42 contract remains intentionally fail-closed unless an exact track+album+edition binding and authorized grant are verified; PHP resolve on its own does not attest exact album+edition.
- The older static source-factory analysis does not prove a live source-before-decoder binding for the **current 2025 host**, and there is no authenticated in-process audio test yet. Do not substitute static method presence for playback evidence.
- Next bounded technical task: establish one exact current-2025 native source selection point and its current track identity using isolated read-only checks, then integrate the existing fail-closed B42 contract at the same player/decoder. No second player, no modifications to Test.50, no release before a real authorized audio/controls test.


### 13 Nov exact audio-observer extension (startup stability still passed)
- Native standalone #43428891020 and paired original-first #43428891031: 25/25 CELIKOM in both, original installed in paired, provider returned without throw; snapshot `d425771accce3443d8edb159021c717a5470d80d` / `backup/android-a1-2025-extractor-arg-reader-labels-25x25-20261113`.
- Both MediaDataSource readAt subclasses and the exact framework MediaExtractor source hook register; source classes now separately categorized but **0 live calls** because login/music not exercised. This does not extend the startup claim to audio, album edition, controls or release readiness. Prior proven Firebase backup unchanged.


### 13 Nov latest exact object-identity witness — native restart regression verified
- Read-only Java source object == reference correlation `a18ee8d705dd08154c4cb904ffcec9aacd2ed475`, backup `backup/android-a1-2025-extractor-readat-same-object-25x25-20261113`; pair [#43436009883](https://github.com/manufact-test/nomusic/actions/runs/43436009883) original installed and clone 25/25, standalone [#43436009850](https://github.com/manufact-test/nomusic/actions/runs/43436009850) clone 25/25, both SUCCESS. Expected 0 MediaExtractor/readAt/same-object match calls in startup-only tests, not an audio/product pass. No Firebase/architecture changes.


### 13 Nov — owner-phone diagnostic APK artifact
- Fresh ARM13 publisher-first workflow [#43450303301](https://github.com/manufact-test/nomusic/actions/runs/43450303301) SUCCESS. Original publisher 25/25, CELIKOM clone 25/25, both installed concurrently; clone-only resource route applied, no Metrica fatal suppression.
- Exported one-time diagnostic APK artifact #14050162270 (71,426,028 bytes), SHA-256 `2d043de0fdabcd9ee4109d01c376d764d4e640b4a4dd07df1bffb6a0264f7e63`, package `pro.celikom.yandex.nativeclonelab`, based on Yandex Music 2025.10.4. Owner phone not touched.
- Two MediaDataSource readAt hooks and exact MediaExtractor source hook registered. No music playback was run in CI: actual readAt/extractor/same-object event counts remain 0. Owner test on existing phone/account is next; this is not audio acceptance.


## 13 Nov — owner-device onboarding crash supersedes audio test

Owner successfully installed the private diagnostic APK with Play Protect passed and saw Yandex My Wave/recommendation intro UI after a 15–20 second first-start wait. At the fourth intro indicator/page, pressing the next arrow starts loading and then closes the app to the Android home screen. Owner cannot reach login, music or playback. This is now the active blocker. Prior workflow #43450303301 only verified an idle foreground MainScreenActivity for 75 seconds and did not automate onboarding taps; 25/25 is not full-app acceptance. No cause inferred yet. Use the existing `capture-diagnostics.bat` BEFORE launching the clone, reproduce the same intro/next action, wait 5 seconds after exit, Ctrl+C and send `CELIKOM-A1-Audio-Diagnostics.txt`. The finite event stream includes FATAL_DISPATCH and explicit process-exit/kill witnesses. No uninstall, data clear, Play Protect bypass, or B42 integration until this failure is diagnosed and fixed.
