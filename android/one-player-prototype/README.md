# CELIKOM Android single-player Gate 0/1 precursor

Isolated, **offline pure-Java source-selection gate**, not a functioning Yandex patch, not an APK and not evidence of access to Yandex internals.

Run: `bash android/one-player-prototype/run-tests.sh` (JDK 8+).

- One decision per track **before** host player load. Caller owns **one** player and the original source.
- Candidate must be approved, entitled, fully cached, integrity-checked, edition-exact, and within a 1.5s duration tolerance. Only a narrow `content://` URI is eligible for a replacement; actual granting and readability must be checked by authorized host.
- No catalog identity inferred from aliases or title matching. Without verified **internal** catalog + edition identity, the original is used unchanged.
- No credentials, login, network requests, proprietary APK, playback interception, root, accessibility, notification listener or second MediaPlayer.
- The reference catalog ID 42884423 for RASKOL is taken from CELIKOM's previous external diagnostics. It does **not** prove an internally retrieved Yandex catalog ID; edition labels here are synthetic test data.
- Integration prerequisite: a legally distributable, auditable host/client with a documented API for catalog identity and pre-load source selection. Without such a host, Gate 1 is **BLOCKED**, not passed.

## Isolated Android lab

The `app/` module is a standalone Android 8+ APK with **one active Android MediaPlayer**, native pause/resume, seek, and a next-item boundary that releases the previous player. It accepts only user-chosen audio files via Android's system file picker. No network, Yandex integration, account access, root, injected hooks, Accessibility or privileged permissions. `MediaMetadataRetriever` reads duration without starting a second playback clock.

Build on a JDK 17/Android SDK 35 host using Gradle 8.10.2:

```sh
cd android/one-player-prototype
gradle :app:assembleDebug
```

The Android lab accepts manually typed IDs as **simulation input only**; it does not and cannot attest real Yandex IDs. It models a trusted first-party host that would supply them. The manifest and APK do not replace official Yandex Music. Its `Next` button demonstrates stopping/releasing the old decoder, then asks for a new local original; it is not a Yandex playlist or radio integration. Never market it as a functioning CELIKOM/Yandex patch. A debug APK is not evidence of Play Protect acceptance.

Build workflow: [android-one-player-lab-apk](https://github.com/manufact-test/nomusic/actions/workflows/android-one-player-lab-apk.yml). The workflow supplies an artifact only for later isolated-device verification; **do not install on the owner's primary device**.
