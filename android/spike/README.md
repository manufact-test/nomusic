# CELIKOM Android PoC 0.2.0

Kotlin/Compose, min API26, target/compile36, JDK17/Gradle8.13. Private PoC identity `pro.celikom.spike`; this is not a Stage17 production release.

The application opens the official Yandex Music website in Android System WebView. The document-start script uses the exact shared extension core, Yandex adapter and OriginalAudioGuard. A native MediaPlayer plays only the signed replacement returned by the existing CELIKOM API. It does not capture audio or modify the native Yandex application. Desktop website mode is an explicit browser display option; region/auth/CAPTCHA/DRM restrictions are not bypassed.

Native controls: CELIKOM login/register/email verification/password reset; encrypted Android Keystore session storage and stable installation ID; independent server refresh session; entitlement and promo activation; replacement/Original. Yandex login stays on allowlisted official HTTPS login pages, with no CELIKOM credentials sent there. Finite dates display Moscow time; lifetime access displays once. Explicit replacement starts trial through the common idempotent activate endpoint. Existing promo access, incident compensation and server reward policy remain authoritative.

The original is guarded only after the replacement is prepared, aligned and started muted. Exact track/media/source/duration binding, pause/seek/next/visibility events and a 1.5-second page lease restore original sound on loss of native heartbeat. The main-frame origin-restricted web message channel can only release a matching lease; it cannot call native account APIs or obtain tokens. Native stale generations, polling timeout, network/access failure and signed URL expiry stop replacement. A confirmed public incident hides music controls and leaves the account available; network errors do not announce an incident. Access is rechecked every5 seconds while replacement plays. Backgrounding/earphone disconnect stops replacement; returning requires explicit Start. Physical audio focus/route/background and actual service playback still require owner verification before Stage17.

Build:

```sh
python3 generate-fixtures.py
node generate-surface-probe.mjs
node --test playback-surface.test.mjs
gradle :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
gradle :app:connectedDebugAndroidTest
```

Native tests use owned WAV sources and isolated API/surface doubles with the production controller; they do not grant real access or alter real accounts/media. The separate real-site probe observes the CI runner's region gate and is not a service playback PASS. Native UI snapshots and APK artifacts are CMS AES-256-GCM encrypted, retention1 day, with recipient private key outside GitHub. Debug signing is not production signing; public APK distribution remains disabled.

Stage16 remains partial until the owner demonstrates exact-state playback/replacement on the permitted real surface. Stage17 remains unstarted; uploads/suggestions/reports/benefits/device management/analytics and full background playback are not claimed ported by this PoC. Backend platform/version headers are sent but not yet stored as mobile device classification. See [surface evidence](../../docs/spikes/android-playback.md).
