# CELIKOM Android native — owner-only public/active MediaSession gate (10.11.2026)

## VERIFIED SIGNED, READ-ONLY APK; NO NATIVE REPLACEMENT

Это продолжение **новой нативной одно-плеерной архитектуры**, а не Test.50, Test.51, DynamicsProcessing или второй MediaPlayer. Цель — выяснить, может ли **уже работающий неизменённый Яндекс на физическом HONOR** предоставить разрешённый платформой доступ к media session, которого не было в анонимном эмуляторе; всё ещё требуется независимое доказательство разрешённой audio source-before-decoder integration. Позитивный Media3 playlist command не означает разрешения проигрывать сторонний URI.

### Code and independent backup

- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
- **Verified source commit exactly built into APK:** `f565c5650fcf018ae946597e0fc47b2ecb50bc53`.
- **Frozen rollback:** `backup/android-native-public-session-gate-signed-ci-green-20261110` points to that exact code.
- **[GitHub Actions #42863386941 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42863386941)**; `security-and-scope` SUCCESS and `build-readonly-gate` SUCCESS, `apksigner verify --verbose` v2 true, no Yandex APK built/modified.
- Actions artifact `13785873114`: `CELIKOM-Native-Public-Session-Gate-0.1-READONLY`, includes a first-party package `pro.celikom.nativegate` APK and proof JSON.
- Standalone file: `CELIKOM-Native-Yandex-Session-Gate-0.1-READONLY.apk` (in conversation workspace copy `CELIKOM-Native-Gate-0.1-READONLY.apk`).
- Exact APK size **8 310 556 bytes**, SHA256 **`1c4672a72dc1a2f2be030e5edff3600a8a2cbe1c5c3c618d5ffc3063d6cd1bd6`**, independently checked against exact downloaded receipt.
- `signed_debug_apk_v2_verified = true` (separate first-party debug certificate, NOT official Yandex signature, not a CELIKOM stable release).
- `physical_honor_verified = false`; no installed Yandex, app state, account, audio or notifications were accessed by CI.

### Native application

Path `android/native-yandex-hooklab/device-session-gate/`; built as separate `pro.celikom.nativegate`.

- UI **«CELIKOM Native Gate»**, very explicit «не замена музыки» disclaimer, three buttons: (1) public exported service without additional permission; (2) already-active Yandex session capability flags; (3) Android notification-access settings.
- `GateActivity` verifies **currently installed Yandex actual publisher signing certificate** against exact original SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`. This uses getPackageInfo, not extraction of private app files.
- First mode attempts to connect ONLY if exactly one public media service, then inspects `Player.COMMAND_CHANGE_MEDIA_ITEMS`, `COMMAND_SET_MEDIA_ITEM`, `COMMAND_GET_CURRENT_MEDIA_ITEM`, `COMMAND_PLAY_PAUSE`, `COMMAND_SEEK_IN_CURRENT_MEDIA_ITEM` as **booleans**.
- Second mode is **optional** and requires Android **NotificationListenerService** access, because documented `MediaSessionManager.getActiveSessions(ComponentName)` requires an enabled listener or privileged permission. It filters to exactly one active `ru.yandex.music` platform session; checks only public PlaybackState action flags `PLAY_FROM_URI`, `PLAY_FROM_MEDIA_ID`, `PLAY_PAUSE`, and optionally available Media3 player command flags from the existing platform token.
- **Important privacy warning:** «Доступ к уведомлениям» is BROAD; Android would allow a listener app to read notification contents, but `NativeSessionListener.onNotificationPosted/onNotificationRemoved` are **no-ops**, no logging, no network, no storage, no analytics, no media capture. The user can decline permission entirely, and should NOT bypass Android restricted-settings or Play Protect if it is blocked. They can revoke the notification access after the check.
- Manifest has no `INTERNET`, `RECORD_AUDIO`, media storage, accessibility, location, installation permission; no data source replacement, playback/queue mutation, login, token/URL/song retrieval.
- `test_device_gate.py`+workflow check the above and reject accidental playback calls, permissions, account or notification reads.

### Owner manual check: ONLY if owner wishes

1. Keep ordinary original installed Yandex.Music, existing login and account. Start playing a song there normally. Neither music library nor app gets replaced or reinstalled.
2. Install `CELIKOM Native Gate` from the signed **separate** first-party APK. Open, tap **«1. Проверить без дополнительных разрешений»**. Send back the **state and boolean flags only**, no screenshot of media/notification content necessary. A failed public-bind is meaningful, not a reason to change the official app.
3. If first mode cannot connect and user is comfortable with its security scope: use the button to Android notification-access settings and *optionally* grant access to `CELIKOM Native Gate`, then tap **«2. Проверить активную сессию»** while Yandex has an actual active session. Send **only state and flags**. If Android prohibits granting access or flags are inaccessible, STOP, no restricted-settings/Play Protect bypass.
4. Revoke the listener access, delete only the probe APK if desired; original Yandex, CELIKOM Test.50/stable and all downloaded media unchanged.

### Outcome gate

- `NO_PUBLIC_SERVICE` / `PUBLIC_BIND_REJECTED` alone isn't full failure; first-party active session may still be accessible under documented user-granted permission. 
- If active Media3 command flags are unavailable or no token, the **supported public one-player surface remains NO-GO** under current environment; do not continue pretending native source swap works.
- Even `COMMAND_CHANGE_MEDIA_ITEMS=true` isn't proof the Yandex player accepts our approved alternate source or preprepare descriptor; separate authorized source validation and trackId+edition+generation + real decoder witness are necessary, before any native CELIKOM replacement version.
- No native sound replacement APK exists yet, no performance/acoustic pass on HONOR, no USB/Bluetooth/device QA.
- Do not return to old Test.50, Android separate double-player, Windows JS, unsafe app-clone, x86 LSPatch/AppMetrica, publisher-signature/DRM bypass or Internet proxy tricks.

**Existing NEW native progress preserved**: `backup/android-native-lero-lmb4-ha4-signed-readonly-chain-ci-green-20261110` @ `6146109d...` and [signed DEX 7/7 preflight #42860839260](https://github.com/manufact-test/nomusic/actions/runs/42860839260); [module/JVM #42860807834 2/2](https://github.com/manufact-test/nomusic/actions/runs/42860807834). Their synthetic/ref counts are not working Yandex decoder proof. Further research depends on the native platform gate / authorized in-process test host evidence.
