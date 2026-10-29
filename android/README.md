> **Android 29.10.2026 — текущий native-компаньон, НЕ WebView PoC.** Этот README про Stage16 исторический. Актуальный проект — `android/native-companion/`, последняя подписанная версия **0.3.51 (отклонена владельцем)**, решение — архитектурная переработка. Инструкции: [NEXT-CHAT](../docs/android/NEXT-CHAT.md), [ARCHITECTURE-RESET-CHECKPOINT](../docs/android/ARCHITECTURE-RESET-CHECKPOINT-2026-10-29.md). Последний signed source сохранён в `backup/android-0351-last-signed-20261029`, промежуточный pre-refactor source — в `backup/android-pre-architecture-refactor-20261029`. Не выпускать ещё одну таймерную 0.3.52 до переработки; desktop/server не трогать.

---

# Android Stage16

[Private PoC0.2.0](spike/README.md) implements real WebView-master/native-replacement flow using the existing shared backend and extension adapter/guard. Technical build/native/controller/crypto/UI checks passed; actual Yandex playback is still pending the owner phone check because the CI runner has a region gate. Stage16 remains partial, Stage17 unstarted, Stage15 excluded.

[Owner check](../docs/spikes/ANDROID-OWNER-CHECK-2026-10-11.md) · [Evidence and boundaries](../docs/spikes/android-playback.md). Foreground-only PoC; do not claim production signing, background playback or full Beta feature parity. No live backend data change/public APK publication/PR6 merge.
