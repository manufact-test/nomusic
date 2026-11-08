# CELIKOM Android Test.74 — opt-in independent Yandex control witness

**Purpose:** identify why native Yandex pause/seek state is stale on **RASKOL** and **«Дым»** yet ordinary songs appear controllable. Test.73 audio engine is unchanged; **Test.74 is a diagnostic, not a fix**.

## Proven Test.73 failure
HONOR Android 13, Yandex 2026.10.3 #170gpr. Combined log `CELIKOM-combined-20261108-223832.txt` + video `SVID_20261108_223656_1.mp4`. See [forensic investigation](ANDROID-TEST73-HONOR-NATIVE-CONTROL-TRUTH-2026-11-08.md). Both bad songs have `MediaController` silent on same-song seek and visible native UI pause while external `isPlaying=true`. CELIKOM decoder native seek ACK after *discovery* is 38–54ms, so tuning decoder is not root cause.

## New approach and limits
Android `MediaSessionManager.getActiveSessions(ComponentName)` is documented to be available when the user manually enables our `NotificationListenerService`, without root or privileged `MEDIA_CONTENT_CONTROL` permission. Read-only Android framework `android.media.session.MediaController` of only `ru.yandex.music` is compared against the existing `androidx.media3.session.MediaController` via a side-by-side timeline.
**This may expose the same stale underlying Yandex state**; that is exactly what the experiment decides, not a claimed solution.

### Test.74 changes (isolated branch)
- New `YandexSessionWitnessService` extends `NotificationListenerService` but does **not implement `onNotificationPosted` / `onNotificationRemoved`** and reads no notification contents. It filters `getActiveSessions` by the Yandex package, registers **passive** playback-state/metadata callbacks and samples **every 500ms** while owner-enabled diagnostics is running.
- Logs `yandex_witness_sample`: selected Yandex session availability and count; raw native framework state, raw and time-projected position with state age; full current title, artist and duration for attribution; existing external Media3 position/isPlaying/playWhenReady; available remote seek/pause commands, `seekable`, `dynamic`, `live` flags. These flags were previously not logged as values. Also logs `yandex_witness_playback_callback`, `yandex_witness_metadata_callback`, `yandex_witness_session_selected`, `yandex_witness_permission`, `yandex_witness_unavailable`.
- `ProbeService.sample()` calls witness **after** `albumProbe.publishCurrent();replacement.update(current);`; no result feeds back to any playing decision, source identity, effects, decoder, transfer, network or entitlement.
- **Only Test APK manifest** receives exported Android system-bound listener guarded by `android.permission.BIND_NOTIFICATION_LISTENER_SERVICE`, action `android.service.notification.NotificationListenerService`; **only Test APK UI** gets a permission-settings button. A confirmation dialog explicitly warns the user that Android grants access to all notifications even though our code intentionally reads only Yandex session state, and that permission is optional/manual and revocable. No separate accessibility, audio, notification-text, microphone or root privileges.
- Signed test package `pro.celikom.nativeprobe.test`, `0.3.85-test.74` code `86160`, filename `CELIKOM-Android-0.3.85-TEST-74-MEDIASESSION-WITNESS-SIGNED.apk`. No production audio, stable 0.3.92, OTA, Hostinger, backend, main or desktop changes.

## Owner HONOR experiment once signed APK is available
1. Install Test.74 over Test.73 (same package/signature). Launch and tap **«Проверить независимое управление Яндекса»**, review disclosure, open Android «Доступ к уведомлениям», manually allow **CELIKOM Test**. Permission can be revoked afterward.
2. Start CELIKOM (normal). Record one screen video and a combined diagnostic TXT.
3. On a **working track**, wait until CELIKOM version is audible, tap **Pause**, hold at least **3 sec**, tap Play, scrub forward about **+60sec**, then backward. Repeat the **same actions on RASKOL** and **«Дым»**. This single A/B is sufficient to compare data; no need to test 100 tracks.
4. Save and provide **one** Test.74 combined log and one video.
5. If independent framework session shows correct paused/seek state at the same moment Media3 remains wrong, we have an alternative *candidate* for correction; implement only with verified same-title/ID/session freshness and safe fallback. If both are stale or no session visible, **reject this path** and investigate genuinely independent signal rather than producing another latency build.

**Stop rules:** no `pause`, `play`, `seekTo`, `getTransportControls`, source gain changes or replacement authorization via witness. No interception of other apps' notifications; do not publish or auto-enable permission. Host tests and CI only prove APK build and absence of commands; only phone A/B establishes utility.
