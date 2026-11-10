# ⛔ REJECTED BY OWNER — DO NOT INSTALL OR CONTINUE (2026-11-09)

**This Android WebView/Yandex website design was built contrary to the owner's explicit product requirement, and was REJECTED.** CELIKOM must work with the native **Android Yandex Music client** where people log in and listen inside Yandex; not within the CELIKOM app/embedded browser. This preview is a source/archive only, not an accepted test APK or a viable product. No more coding, installation requests, or promotion of this branch. See `docs/android/ANDROID-NATIVE-YANDEX-RESTART-OWNER-OVERRIDE-2026-11-09.md` on branch `research/android-single-player-inprocess-20261109`.

---

# CELIKOM Android — real Yandex Music web integration, rootless candidate

**Separate preview, not a stock Android Yandex patch and not a release.** This app opens the **actual `https://music.yandex.ru` website inside Android WebView** rather than fabricating a new player. Its source-gate tries to provide a cached approved track as the **same page media element's source before play**; no CELIKOM MediaPlayer, AudioTrack, equalizer or parallel playback clock. Android's native client `ru.yandex.music` is unaffected.

The existing CELIKOM Chrome extension uses a second `<audio>`, which is **deliberately not copied**. Only its read-only track identity adapter and catalog parser are reused in the web page. A native authenticated CELIKOM broker fetches approved MP3s into app-private cache. A synthetic same-origin resource is served by WebViewClient (range support) so the original Yandex HTMLMediaElement can play it directly, if supported by Yandex web player.

## Important truth / limitations

- This uses Yandex **web** UI, **not the official installed Android client**. We must check website login, features, radio, background controls, actual browser media implementation, CSP and Play Protect on a device before calling it functional.
- If host track ID is ambiguous or the asset is not cached, it **leaves the original alone**. A first uncached play may play the original and prefetch the alternate for later. It may be unsupported when Yandex web player has an opaque MSE pipeline or controls that recreate its audio element.
- Yandex credentials stay on Yandex's own login website; the CELIKOM login is separate in native controls. The JS bridge is registered ONLY on `https://music.yandex.ru`, rejects non-main frames, and does not expose tokens or arbitrary network methods.
- User must give consent for login in embedded WebView. WebView cookie storage is isolated from official Yandex app, and Yandex may reject embedded login.
- No root, APK tampering, CA interception, SSL bypass, Accessibility, Notification Access or disabling Play Protect. No proprietary Yandex APK is included or redistributed.
- The stock Yandex app, accepted Test.50, server, catalog, stable, and OTA remain unchanged.

### Build

`cd android/yandex-web-oneclock && gradle :app:assembleDebug` with JDK17, Android SDK35 and Gradle8.10.2.

The debug build's CI proves compilation and offline tests only. Full acceptance requires a real device with Play Protect ON and a CELIKOM test account; do not ask the owner to use their normal Yandex account until security review.
