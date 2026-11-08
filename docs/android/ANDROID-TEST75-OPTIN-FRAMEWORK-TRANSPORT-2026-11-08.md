# CELIKOM Android Test.75 — verified native framework PAUSE/SEEK repair (opt-in)

**Source:** Test.74 live HONOR video and combined TXT, summarized in [ANDROID-TEST74-HONOR-PROVEN-YANDEX-REMOTE-LAG-2026-11-08.md](ANDROID-TEST74-HONOR-PROVEN-YANDEX-REMOTE-LAG-2026-11-08.md).

## Diagnosis
Actual Android system Yandex media session receives same-item seeks 3.10–3.28 seconds before AndroidX Media3LibraryService controller. Framework receives actual PAUSED for Dym (3.60s) and RASKOL (1.83s) while old Media3 incorrectly reports playing=true. Our decoder seeks in ~32–58ms after the outdated signal arrives. Good «Холодно» shows immediate same-item Media3 SEEK event. Source metadata: same title and artist and duration, seekable=true, live/dynamic=false.

### Constraint
Android 13 `MediaSessionManager.getActiveSessions` public API requires enabled notification listener, otherwise privileged `MEDIA_CONTENT_CONTROL`; there is **no permission-free equivalent evidenced**. Earlier direct platform MediaBrowser on Yandex Media3LibraryService failed at connect. Never bypass Play Protect, never silently enable listener or request Accessibility/root.

## Test.75 change
- Separate test branch `feature/android-0385-test75-framework-transport-optin-20261108`, APK `CELIKOM-Android-0.3.85-TEST-75-OPTIN-NATIVE-PAUSE-SEEK-SIGNED.apk`, package `pro.celikom.nativeprobe.test`, version code `86161`. Builds on exact Test.74 and keeps Test.73 source matching/Quest and audio engine.
- `YandexSessionWitnessService.controlSnapshot()`: read-only framework media position, playback state, title, artist, duration, state timestamp, speed. It filters only `ru.yandex.music`. No notification content, no transport commands.
- `YandexFrameworkTransportPolicy`: pure Java, starts in unchanged legacy mode; switches **only** when exactly one enabled Yandex system session has same canonical title+artist and duration <=2s different, state fresh, and **real remote-vs-framework discrepancy** (seek gap >=1600ms or framework PAUSED while remote still playing). Never switches just because remote briefly buffers. After selecting authority for that source alias, follows actual framework position, buffering and native pause/resume. Identity mismatch, missing listener/session, revoked permission or stale state **fail closed to original** for the rest of the same track rather than continuing a falsely playing replacement. Next track may resume baseline.
- In `ProbeService.sample`, policy runs after verified Test.72 cross-track metadata and after old media 3 session fence, but before `PlaybackSource` and `replacement.update`. A confirmed native seek calls the existing `replacement.sourceSeekRequested` event exactly as usual; no new direct decoder/player commands are made. `YandexSessionWitnessService.sample(c,rawMedia3)` continues to log raw remote values for A/B, not corrected ones.
- `Test75FrameworkTransportPolicy` hosts RASKOL and «Дым» replay: two early seeks, hidden native pause, resume, original on revoke; good track remains unmodified, wrong artist/title/duration and duplicate sessions disallowed, stale buffering/paused rejected. Existing Test72, all Test73 regression/source-snapshot and packaging verifier remain required.

## Verified signed delivery
- **Accepted source SHA** `cf294892f1dc8b60c56038d19bfbbc5ff5192bab`.
- [Full native regression + signed test CI: **SUCCESS** (42521506931)](https://github.com/manufact-test/nomusic/actions/runs/42521506931). All validation, final artifact verifier and signing passed. Source checked out by exact SHA from validated run.
- APK `CELIKOM-Android-0.3.85-TEST-75-OPTIN-NATIVE-PAUSE-SEEK-SIGNED.apk`: **8,906,905 bytes**, SHA256 `44f2fdb3e491c9ac519938a9bfabff74af7453467a8a05a6c0b33fab5a21f407`; v3 signature verified with prior test cert SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Installed stable not touched.
- Personal Library verified upload: [APK](https://chatgpt.com/library?file_id=libfile_c09e72a838548191a4625c2206e238e0&account_id=personal), plus [verification JSON](https://chatgpt.com/library?file_id=libfile_4341f34d11f08191acdc5a140d38d31a&account_id=personal) and [receipt JSON](https://chatgpt.com/library?file_id=libfile_a8b705a37fc88191b0348399d52c1785&account_id=personal).
- This signed APK is **NOT hardware-verified on HONOR** and **NOT approved as a production fix**. Android notification-listener access remains genuinely optional and sensitive. Do not ask owner to disable Play Protect.
- Archive last known-good Test.73/74 is unchanged; no changes to stable 0.3.92/OTA/backend/library.

## Acceptance procedure on HONOR
1. **Google Play Protect ENABLED.** Install signed Test.75 update over Test.74. If Android security blocks, **do not disable protections**; collect full exact warning and stop. For app's function, opt-in notification access to CELIKOM Test is required only if the user accepts granting Android's *broad* notification-listener privilege; it may be revoked at any time.
2. With access, play one ordinary song and verify normal manual Pause and forward/back seek.
3. On RASKOL, then «Дым», after replacement audible, native Pause >=3sec, resume, seek forward ~60s and backward ~30s, verify no 3s wait and no audio continues during pause.
4. Send combined diagnostic TXT/video. Look for `source_framework_authority_verified`, `source_framework_seek_detected`, `replacement_pause`, `replacement_hot_cached_seek_request`, no unexpected `source_framework_authority_lost`.
5. With permission revoked, replacement should revert to Test.73 baseline for **new** tracks; on active framework-controlled song it should safely return original. This fail-closed behavior not yet physically validated.
6. No claim of full cure until physical HONOR confirms both problematic songs and normal track and permission behavior.

## Security / product follow-up
User had to disable Play Protect to install Test.74. Unacceptable production workflow. This APK is a **temporary research build** and still depends on an optional powerful permission; distribution warning may recur. Never advise further disabling of Play Protect. Production needs permission-transparent design, trusted signing/distribution and user choice; if no acceptable permission flow, retain original playback fallback. Source, desktop, Hostinger, stable app and original OTA must remain untouched.
