# CELIKOM Android — актуальная навигация к передаче (10.11.2026)

**Начальная точка:** `docs/android/START-NEXT-CHAT-ANDROID-NATIVE-2026-11-10.md` — готовый текст первого сообщения новому разработчику.

## НОВЕЙШАЯ CI GREEN ТОЧКА — оригинальный FileInfo → typed model → реальный Le48 field (10.11.2026)

- **Проверенный код:** `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`. **Бэкап:** `backup/android-signed-typed-dispatch-field-audit-ci-green-20261110` → ровно `78b0437f17888ce49a4c1bea0ba06ca96cb455b9`.
- **Читать первым:** `docs/android/ANDROID-NATIVE-SIGNED-TYPED-DISPATCH-EVIDENCE-2026-11-10.md` — реальные DEX данные от Lhee/Lged через Leed/Ldiv → Lygv.r → Ljgv → Lcq7/Lo4y/Larv; неоднозначный 16-way Le48 dispatch и точный writer/reader аудит двух разных Le48-полей класса Lga4.
- **CI SUCCESS:** [typed coroutines #42808158803](https://github.com/manufact-test/nomusic/actions/runs/42808158803), [Ldiv/Ljgv consumers #42808680756](https://github.com/manufact-test/nomusic/actions/runs/42808680756), [media candidates #42810750855](https://github.com/manufact-test/nomusic/actions/runs/42810750855), [virtual dispatch #42809849405](https://github.com/manufact-test/nomusic/actions/runs/42809849405), [exact field writer #42810607588](https://github.com/manufact-test/nomusic/actions/runs/42810607588), [Android module #42810750850](https://github.com/manufact-test/nomusic/actions/runs/42810750850) SUCCESS 2/2.
- **НЕ decoder proof:** найденная семишаговая близость к Lro7.y0 зависит от выбора одного из 16 виртуальных receiver и разных switch-веток. Фактически Lga4.c использует Le48 field-2, а конструктор инициализирует Lzcd в ДРУГОЙ field-1. Field-2 наблюдался с Lya4/Lkc6 и неизвестными writes, без подтверждённого current-track source. Android audio replacement по-прежнему НЕТ.

## Предыдущая подтверждённая точка

- **Точный проверенный код:** `8b7bc64f89249e5434da739851bececce2adb121` — [signed DEX CI #42806655214](https://github.com/manufact-test/nomusic/actions/runs/42806655214) SUCCESS, [Android module CI #42806655152](https://github.com/manufact-test/nomusic/actions/runs/42806655152) SUCCESS 2/2.
- **Rollback:** `backup/android-signed-register-cfg-ci-green-20261110` → `8b7bc64f89249e5434da739851bececce2adb121`.
- **Сначала изучать:** `docs/android/ANDROID-NATIVE-SIGNED-REGISTER-COROUTINE-CFG-EVIDENCE-2026-11-10.md`. Выявлены Lxa7.<init>, Lged.a → Lhee.a и прямые coroutine callers; это may-flow, не Android decoder proof.

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
- **Предыдущий проверенный код (shared-caller этап):** `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- **[Подписанный APK статический CI #42804081064 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42804081064)**.
- **[Android Xposed read-only модуль CI #42804081053 — SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42804081053)**.
- Резервная ветка точно проверенного кода: `backup/android-signed-source-bridge-media-session-ci-green-20261110` → `d7d3f8b82b6d752ed7837dd9955ccb51df71641d`.
- До нового аудита: `backup/android-pre-real-signed-bridge-proximity-audit-20261110` → `0a1f035113fb826f88ebf827a46e5edc66635c7f`.
- Эталон владельца **Test.50** (реально проверен ref `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`): `backup/android-test50-exact-source-owner-accepted-20261106`; не изменять.

**Реальный статус:** Windows CELIKOM **да**, Android CELIKOM source substitution **нет**. Нужна действительная граница текущего decoder source; MediaSession — не она. Не выдавать исходный SDK/CI за реальный audio PASS, не переустанавливать Яндекс на основном телефоне.
