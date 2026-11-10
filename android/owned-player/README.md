# CELIKOM First-Party Android Player — OWNED fallback (NOT a Yandex clone)

**Branch:** experiment/android-owned-player-delivery-20261110. Prototype only; no user APK distribution. Android native source injection Gate A and full Yandex catalogue license Gate B both failed to identify a supported integration. Do not bypass Play Protect or Android sandbox.

One first-party Media3 ExoPlayer + MediaSessionService. The app streams **only** CELIKOM approved replacement grants from its own authorised backend. It has CELIKOM login, explicit activation of the server-owned trial, approved metadata catalogue search, sequential next-track handling, pause, seek and background media session. No vendor Yandex APK, WebView, private APIs, OAuth interception, cloned UI/assets, spyware or dual-player overlay.

**Important product limitation:** the metadata catalogue is only CELIKOM-approved replacements. Access to the complete Yandex Music commercial catalogue is **not** included and cannot be inferred from an individual's Yandex subscription. Rights to distribute the CELIKOM tracks must be confirmed independently before public release.

**Local test:** run `java OwnedContractTest` after compiling `OwnedPlaybackContract.java`, `OwnedQueueFence.java`. Android build: `gradle -p android/owned-player :app:assembleDebug`. CI does NOT publish binaries.

**Must verify before sending any private owner build:** full server contract/account/trial + expired grant test (mock backend), signing/reputation/Play Protect, real foreground service audio on independent ARM Android, notification/media controls, seek/Next/Bluetooth/headphones, permission review and paid-access failure. This README is not proof of audible playback.
