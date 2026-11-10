> **НЕ СОГЛАСОВАНО / РАЗРАБОТКУ НЕ ПРОДОЛЖАТЬ (10.11.2026).** Это ошибочно созданный прототип самостоятельного плеера без каталога официальной Яндекс.Музыки. **Главное ТЗ:** отдельное приложение CELIKOM РЯДОМ с отдельно установленным официальным Яндексом. Клоны и WebView — только обсуждавшиеся, НЕ утверждённые запасные варианты. Код не выбран, не тестировать у пользователя, APK не отправлять. См. [актуальное ТЗ](../../docs/android/ANDROID-PRODUCT-REQUIREMENT-OWNER-CLARIFICATION-2026-11-10.md).

> **STOP / НЕ СООТВЕТСТВУЕТ ПРОДУКТОВОМУ ТЗ (10.11.2026).** Владелец уточнил: CELIKOM должен включать саму Яндекс.Музыку с пользовательским каталогом, «Моей волной» и плейлистами. Этот Media3-only prototype показывает только approved CELIKOM replacements и поэтому неприемлем как основная Android-версия или fallback. Не продолжать разработку, не отдавать APK и не выдавать CI за продукт. См. [исправленное ТЗ](../../docs/android/ANDROID-CORRECTED-PRODUCT-REQUIREMENT-YANDEX-INSIDE-CELIKOM-2026-11-10.md).

# CELIKOM First-Party Android Player — OWNED fallback (NOT a Yandex clone)

**Branch:** experiment/android-owned-player-delivery-20261110. Prototype only; no user APK distribution. Android native source injection Gate A and full Yandex catalogue license Gate B both failed to identify a supported integration. Do not bypass Play Protect or Android sandbox.

One first-party Media3 ExoPlayer + MediaSessionService. The app streams **only** CELIKOM approved replacement grants from its own authorised backend. It has CELIKOM login, explicit activation of the server-owned trial, approved metadata catalogue search, sequential next-track handling, pause, seek and background media session. No vendor Yandex APK, WebView, private APIs, OAuth interception, cloned UI/assets, spyware or dual-player overlay.

**Important product limitation:** the metadata catalogue is only CELIKOM-approved replacements. Access to the complete Yandex Music commercial catalogue is **not** included and cannot be inferred from an individual's Yandex subscription. Rights to distribute the CELIKOM tracks must be confirmed independently before public release.

**Local test:** run `java OwnedContractTest` after compiling `OwnedPlaybackContract.java`, `OwnedQueueFence.java`. Android build: `gradle -p android/owned-player :app:assembleDebug`. CI does NOT publish binaries.

**Must verify before sending any private owner build:** full server contract/account/trial + expired grant test (mock backend), signing/reputation/Play Protect, real foreground service audio on independent ARM Android, notification/media controls, seek/Next/Bluetooth/headphones, permission review and paid-access failure. This README is not proof of audible playback.
