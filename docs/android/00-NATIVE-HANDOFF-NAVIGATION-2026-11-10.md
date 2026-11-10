# CELIKOM Android — актуальная навигация к передаче (10.11.2026)

**Начальная точка:** `docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md` — готовый текст первого сообщения новому разработчику.

## Главное, читать по порядку

1. **Новый результат подписанного Android APK:** `docs/android/ANDROID-NATIVE-SIGNED-SHARED-CALLER-MEDIASESSION-EVIDENCE-2026-11-10.md` — 6 DEX / 837 500 вызовов, прямой FileInfo caller `Lhee;->a`, model consumer `Lged;->a`, без ложного decoder proof, 2+2 прямых вызова MediaSession.
2. **Актуальный краткий статус + исторические ссылки:** `docs/android/NEXT-CHAT.md`. В этом накопительном документе старые «LATEST» и старые SHA — архив; верный кодовый SHA см. выше.
3. **Windows, реально работающий продукт:** `docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md` и `docs/windows/W57-OWNER-0247-REAL-AUDIO-SUCCESS-20261110.md`; код `windows-companion/w22/native-resource-adapter.mjs`. Windows `0.24.7` пользователь принял.
4. **Что из Windows уже аккуратно перенесено в Android:** `docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md` — строгий grant, Track ID, Next, Stop, поколения.
5. **Где находятся реально существующие кандидаты ExoPlayer:** `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md` — четыре обфусцированных класса и отрицательные результаты поиска.
6. **Старые исследования/отказы:** `docs/android/ANDROID-NATIVE-SIGNED-SOURCE-HOP-EVIDENCE-2026-11-10.md`, `docs/android/ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`; они нужны, чтобы не повторять x86/clone тупики, а НЕ как главная задача.

## GitHub, проверка, откат

- Репозиторий: https://github.com/manufact-test/nomusic
- Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`; перед работой считать текущий HEAD, docs-коммит может быть новее кода.
- **Проверенный код:** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- **[Подписанный APK статический CI #42804081064 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42804081064)**.
- **[Android Xposed read-only модуль CI #42804081053 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42804081053)**.
- Резервная ветка точно проверенного кода: `backup/android-signed-source-bridge-media-session-ci-green-20261110` → `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- До нового аудита: `backup/android-pre-real-signed-bridge-proximity-audit-20261110` → `0a1f035113fb826f88ebf827a46e5edc66635c7f`.
- Эталон владельца **Test.50**: `backup/android-test50-exact-source-owner-accepted-20261108`; не изменять.

**Реальный статус:** Windows CELIKOM **да**, Android CELIKOM source substitution **нет**. Нужна действительная граница текущего decoder source; MediaSession — не она. Не выдавать исходный SDK/CI за реальный audio PASS, не переустанавливать Яндекс на основном телефоне.
