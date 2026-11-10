# CELIKOM Android — Windows W57 audio breakthrough review | 2026-11-10

## Proven on Windows, not Android

REAL OWNER-ACCEPTED Windows CELIKOM 0.24.7 audio replacement succeeded in the installed Windows Yandex Music application. The user actually heard approved substitute music. The Windows W57 evidence recorded 2 native signed Media GET HTTP 206, 0 HTTP 403. The owner's audible verdict is stronger than the network-only evidence, but does not prove pause/seek/radio robustness.

Source evidence: https://github.com/manufact-test/nomusic/blob/891be4647a087d542d322fd910e6e03b17ef66e4/docs/windows/W57-OWNER-0247-REAL-AUDIO-SUCCESS-20261110.md

Windows W56 root cause: the publisher-signed **desktop Electron** DownloadInfoSource.src appended ?vsid=...&source_index=... to already signed CELIKOM audio media URL with ?token=...&expires=...&sid=..., causing PHP to reject the corrupted sid as HTTP 403. Narrow guard ONLY on approved media URLs preserved the signed query, HMAC/session/expiry validation, native #t seek fragment and Range 206. No server signing or entitlement security was relaxed.

Source mechanism: https://github.com/manufact-test/nomusic/blob/891be4647a087d542d322fd910e6e03b17ef66e4/docs/windows/W56-NATIVE-TELEMETRY-QUERY-HMAC-GUARD-20261110.md

## What can be reused for Android

- Proven first-party approved catalog grant and secure HTTP Range audio endpoint can stream at least for the DESKTOP request path. The Windows 206/audible success does not prove Android compatibility or grant semantics on Android.
- Verify the *actual final native media request URL* if/when Android native audio source injection is built. Do not confuse a grant URL with the final URL after player transformations. Revalidate strict token/expires/sid; do not bypass HMAC or Play Protect.
- **Do not copy Windows query padding into Android now**: Android native 2026.10.3 #170gpr is a different engine, with FileInfoDto -> sw7.y0/z0 -> eed candidate. No observed Android ?vsid or query-corruption path. Copying an unobserved workaround would be speculative and may break Android.
- Windows uses its own desktop bridge/renderer, not a direct Android 1:1 in-process hook. Native Android pre-prepare decoder source and exact current trackId+edition+generation remain UNPROVEN.
- Freeze accepted Windows 0.24.7. Do not edit Windows branch, server, production or user PC from this Android investigation.

## Android next evidence and guardrail

At the experimental branch, a nonmutating Android public MediaSession.setPlaybackState witness now reports aggregate PLAYING/PAUSED/BUFFERING/ERROR enum categories. JVM model NativePlaybackStateProbe tracks rapid public state toggles; potentially useful for the original user Play/Pause problem if an isolated native ARM host becomes available. But published state is NOT the actual decoder, and multiple sessions or actual user pauses can look like glitches.

No real Android Yandex hooking or audible source replacement is proven, no APK for owner install. Keep Android Test.50, HONOR, original native Yandex, Windows 0.24.7, server and production intact. Do not request paid ChromaSync or Yandex outreach.

Backup prior to this change: backup/android-native-before-windows-breakthrough-review-20261110 = 22d5ef250b94d8ff6a286e1229cd790843de5e43.
