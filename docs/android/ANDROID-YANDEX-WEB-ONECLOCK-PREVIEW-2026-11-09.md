# ⛔ OWNER REJECTED — WEBVIEW IS NOT CELIKOM ANDROID'S PRODUCT (2026-11-09)

The owner explicitly requires **native Android Yandex Music** (Yandex account/login inside its own Android client), with CELIKOM modifying audio in THAT player's process. The Android WebView preview below is intentionally **archived / rejected**, not approved for installation, manual testing, release, or further development. Automated CI SUCCESS only proved a web preview APK compiled; it never proved native Yandex integration, Play Protect approval, or actual music playback. **Do not present this APK to the owner again.** Current correction and correct next-chat task live in `research/android-single-player-inprocess-20261109/docs/android/ANDROID-NATIVE-YANDEX-RESTART-OWNER-OVERRIDE-2026-11-09.md`.

---

# CELIKOM Android — real Yandex Web one-clock preview (2026-11-09)

## Decision and limits

This is an **isolated candidate with real Yandex Music website**, not the installed proprietary native `ru.yandex.music` APK and not a validated finished product. It is the only presently buildable, rootless candidate in this branch for original Yandex UI plus one media clock; it does **not** secretly patch Yandex or emulate a full independent Yandex client.

Branch `feature/android-yandex-web-oneclock-20261109`, directory `android/yandex-web-oneclock/`. Baseline `5964ef8532f7ac5a96edddcbf7b1bc8145935671`. Stable CELIKOM, test-50, original Yandex phone app, server, authorization backend, catalog files, PC/browser, and OTA are unchanged.

### Implemented in one APK

- WebView loads genuine `https://music.yandex.ru/`, with separate CELIKOM Start/Stop, CELIKOM login + email verification + logout. Yandex account login remains exclusively on Yandex pages, cookies not exported.
- Bundle existing CELIKOM Yandex web page identity adapter and track parser from `extension/src/player/core.ts` and `extension/src/adapters/yandex-music-adapter.ts`; no browser extension replacement player copied.
- Document-start only at exact `https://music.yandex.ru` origin. Read-only identity from a matching catalog track id, independent album id, compatible duration. Native receives only track id/album/duration over main-frame-only scoped WebMessageListener; no Yandex cookies, tokens, passwords or network credential data.
- Native CELIKOM encrypted session broker authenticates with unchanged production backend, checks active entitlement/activation, approved-only resolve, short-lived signed MP3 stream, SHA-protected API validation, downloads with safe cap, verifies duration, caches in private storage.
- A random nonce and exact id+album route `/__celikom_audio/<nonce>/<trackId>/<albumId>.mp3` receives an HTTP Range-compliant virtual response from app-private cached audio with 206/416. Access disabled without active CELIKOM+sign-in.
- When permitted cached audio is present and verified **before Play**, the page's **existing** Yandex HTMLMediaElement source is set to virtual MP3 before its native `play()` call. No `android.media.MediaPlayer`, `AudioTrack`, new DOM `<audio>` or synchronized second player. Native host Play/Pause/Seek/Next remain on its own element; source errors before any alternate audio plays attempt a once-only original rollback on that same element, never a mid-song original-to-alternate switch.
- If source not cached, original Yandex remains selected; a native prefetch may make later playback available. **This means first-uncached play is NOT solved**. No fake instant playback claim.
- No root, app signature override, stock Yandex uninstall, Accessibility, broad listener access, custom CA, Play Protect bypass, borrowed OAuth tokens, third-party patch binaries or proprietary Yandex APK distribution.

### Verified reproducible build

- [GitHub Actions run #42584183770: SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42584183770) for source commit `aad5493303445642451d82f99bedb936c2d46c9e`.
- Node same-host source selection tests (including original fallback, edition mismatch and no mid-song oscillation): PASS.
- Existing CELIKOM web adapter regression suite, copied into CI fixture: PASS.
- Java byte-range/seek policy tests: PASS.
- No independent output engine and no high-risk Android permission: source scan PASS.
- Android 35 debug Gradle APK build, SHA256, GitHub artifact upload: PASS.
- Actual extracted APK SHA256: `2f11857c7cbd8275fd75371a53b14dbb78bf62165b02f7ee30f10ded53ceba7b`. APK 3,201,752 bytes, ZIP integrity checked.
- User's personal Library upload **succeeded** to `/CELIKOM/Android/Research/OnePlayer-Web-20261109/CELIKOM_YANDEX_WEB_ONECLOCK_PREVIEW_20261109.apk`; ZIP also saved in same directory. No plain GitHub-only link required.
- APK uses temporary Gradle **debug signing**, not release-signature/OTA; next builds cannot assume signature stability.

### Not proved / mandatory field acceptance

1. Whether current Yandex Music site in HONOR Android 13 WebView permits login, playlist/wave playback, background play and original source selection on its mobile web build. Real user Yandex account remains private; no automated login tests.
2. Whether WebView's Yandex web player continues to honor a replaced media-element URL or overwrites it, especially for MSE/blob tracks and Next/radio. The app now reports a non-secret `alternate-playing`, `host-overwrote-source`, `original-startup-fallback` trace.
3. Actual Play Protect ON verdict on a user device and whether browser/WebView sign-in works; no claims.
4. One-clock audio playback/seek/pause/Next on RASKOL / Дым / control and random queue/first-uncached track. Crossfade Bluetooth and background still unverified.
5. Yandex terms/distribution, third-party mark/UI, host platform updates and subscription restrictions require legal/technical review prior to mass release. This is not the same as original native Yandex Android; user may reject it for lower functional equivalence.
6. A full original-native-package in-process replacement remains blocked by signed APK sandbox; no rootless normal install with trusted official package source takeover has been demonstrated.

### Minimum manual testing once owner agrees

Install **only this distinct CELIKOM preview package**, keeping original Yandex unchanged. Leave Play Protect ON; stop on harmful-app warning, do not bypass. Start app → check Yandex website login and web music actually plays (native original). Separately sign in CELIKOM and enable; first-uncached song may play original. On repeat, observe status and seek/Next. Any Yandex login/security issues = stop. Don't test/claim as production release.

Do not request USB/ADB/exporting Yandex APK, disabling Play Protect, uninstalling original, or moving server/accepted Android checkpoint.
