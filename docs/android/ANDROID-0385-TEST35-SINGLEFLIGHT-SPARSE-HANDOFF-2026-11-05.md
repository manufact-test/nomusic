# CELIKOM Android 0.3.85 — Test.35 single-flight sparse ownership handoff

Date: 2026-11-05. **Experimental side-by-side Test APK only.** Owner acoustic acceptance: **PENDING**.

## Non-negotiable rollback / reference

- Last owner-accepted audible benchmark: **Test.33**, functional commit `53d94d66a32b332b62848e0895285d81dda226e9`.
- Immutable reference branch: `backup/android-0385-test33-owner-accepted-20261105`.
- Independently preserved accepted signed APK: Library `libfile_0924722c86908191bef31db36cfcf0ed`; SHA-256 `7c51a7a394e53462b171ed3250953fbb7ab840a54587b4c89548aa957489a5e3`.
- Owner-accepted full rollback ZIP: Library `libfile_670135d6fbec81919cbac9cc1e75a4cb`.
- Test.34 `f8760d5410f00cfa95f6629b1391f98936a4432d` was **rejected by owner**; do not advance from it. Previous diagnostic `CELIKOM-combined-20261105-105846.txt` and screen recording `SVID_20261105_105656_1.mp4` are evidence, not new release sources.
- Do not overwrite, rebase, force-update or retag any Test.33 backup. Do not touch stable Android `pro.celikom.nativeprobe`, stable OTA, PC, Hostinger, API, Admin, track-ID strategy or golden finger-seek behavior.

## Field finding that motivated a different approach

Test.34 first six warm joins: about 568 ms mean; next ten: about 1,555 ms mean. Delayed joins observed at approximately 2.67 seconds and 3.39 seconds; an additional speculative grace attempt made no join by ~50.3 seconds on one sample. The user's primary report is that some previously fine tracks did not switch until ~35 seconds. These figures describe specific diagnostic samples, **not** comprehensive performance distributions.

Previous mechanism: speculative **full-file** NEXT copy on a separate worker; when next song became current while the copy was unresolved, current could wait up to 1,200 ms and then create a **new sparse Range transport**, forfeiting the initially downloaded bytes. Serial resolve work can still contribute delay; no claim that this patch fixes every slow identity or network path.

## External source research (principle, not copied code)

- [`ym-liberty-android` app.js at pinned commit](https://github.com/gagayhhad-tech/ym-liberty-android/blob/35f50c85391c3f2e871a44bf366523e19973f217/android_app/assets/www/app.js): keyed `streamCache`, promise coalescing, and a prepared `preloadPlayer` handed to `playTrack`; a different player architecture, so only **resource reuse/ownership** transfers to CELIKOM.
- [Android Media3 cache data sources](https://developer.android.com/media/media3/exoplayer/customization): validated cache bytes can be shared by a stable source, rather than fetched again during a playback handoff.
- [Android Media3 preloading](https://developer.android.com/media/media3/exoplayer/preloading-media/preloadmanager-concepts): next-media preparation is deliberately separate from eventual current-media playback, with current playback given priority.

## Test.35 functional implementation

1. **One `BufferedAudio` instance per speculative NEXT**, running the already vetted HTTP 206 + validators + 128-KiB independently preemptible Range blocks. It prepares start/end metadata and optionally continues background caching.
2. A `PromotableAudioLease` enforces NEXT account/alias/track identity, and on handoff changes ownership to the fresh current-track/operation/account lease. Stale and revoked resources cannot be resurrected.
3. Fresh `CURRENT` resolve **always happens**. The source is adopted only if album/alias, track ID, account, replacement edition key and measured duration agree.
4. If NEXT has finished sparse initialization, **the exact source and verified byte map** are handed to the foreground decoder, without a duplicate foreground HTTP stream or full-file transfer. Its current decoder reads have foreground priority.
5. If NEXT resolve/first-block initialization is still pending, it is revoked and the current foreground sparse setup begins immediately, **with no 1.2-second speculative progress wait**. A completion callback after revocation must close its unused source.
6. If NEXT fully caches before the boundary, it uses **the untouched Test.33 local-file + silent primed-decoder path**; this is a fast cache special case, not a new audio blend.
7. New code is opt-in only for the Test APK's real `ProbeService`; existing three-argument `ReplacementEngine` paths remain unchanged for frozen regression callers.

No new notification permissions, accessibility, VPN/audio capture permission, player replacement, pause/seek manipulation, source gain tweak or DRM workaround. The app continues to leave the Yandex source audible until the validated exclusive handover. The patch cannot guarantee zero delay for songs without next metadata, unavailable replacement, invalid signed URL or slow fresh resolve; those require field logs.

## Validation requirements before giving APK to owner

- Entire real-engine native host suite, plus `Test35SingleFlight.java`: source object identity, verified bytes retention, late callback disposal, wrong-edition fail-open, current-priority fallback, account/operation lease takeover, full-file primed reuse, rapid Next.
- Static parity: **the actual `ProbeService` constructs the four-argument opt-in engine**; the architecture lease gate includes the new owner transfer.
- Golden Android 0.3.85 seek, pause, old source gain, and audio authority contracts must remain green.
- Android API 36 Java compilation, D8, original APK base checksum and signing certificate, verified v3 signature, separate `.test` package, updater absence, no stable manifest authority, full APK + verification + JSON receipt artifact.
- Human **HONOR 50 / Android 13**, after artifact is confirmed: listen to familiar album, mixed random picks and the especially heavy transitions; then provide one combined log/screen record. Side-by-side qualitative comparison must use **Test.33** as gold. Do not promote a CI pass to acoustic acceptance.

Test.35 candidate branch: `feature/android-0385-test35-transfer-ownership-20261105`.
Exact remote functional signed source **`6bf318640b969605c352e3e1c4bb44174f91ff58`** (tree `8c206d78b4a3e044c2634057660c1d304356ad70`; local independent same-tree commit `2e397d4252133d9256096c5e0030ce99415a0f4f`).
Dedicated signed-candidate restore ref: **`backup/android-0385-test35-signed-pending-20261105`** pinned to that functional SHA. It is not an owner-accepted replacement and must not displace the Test.33 backup.

Android native regression and signed-test builder: **[GitHub Actions #41995295434 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41995295434)**. Original base SHA and signer match. Version `0.3.85-test.35`, code `86120`, package `pro.celikom.nativeprobe.test`, size `8,820,889` bytes, final signed APK SHA-256 **`7371b87b2af31b2ac652cfa2a6a25ba6e631dc388da489fda1b4b13c37a7498c`**. v3 signature verified; v2 is not present/verified and was not required. Stable OTA untouched; no stable publish job executed. Artifact ID `13400476202` contains all **three** required files, separately unzipped and receipt/verification digest checked.

**[Permanent signed Test.35 APK](https://chatgpt.com/library?file_id=libfile_82d59f4b91f08191a11acead57161515&account_id=personal)**. Experimental **owner HONOR physical playback / acoustic acceptance PENDING**, not a replacement for Test.33. The signing workflow proves successful build/structure, not a seamless handover on-device.
