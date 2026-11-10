## UPDATE 10.11.2026 — signed native ExoPlayer implementor truth (LATEST)

**Verified code commit:** `fcd7550b86ee93082ff3a8b119e38b29d02482d8`. **Rollback backup:** `backup/android-native-real-media-implementation-evidence-20261110`.

- [Native original media engine CI #42791262439](https://github.com/manufact-test/nomusic/actions/runs/42791262439) **SUCCESS**: standard class `ExoPlayerImpl` absent, `ExoPlayer` interface defined.
- [Exact DEX type hierarchy #42791641169](https://github.com/manufact-test/nomusic/actions/runs/42791641169) **SUCCESS**: 4 obfuscated concrete implementors `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`, not necessarily player/decoder for current audio.
- [Inherited prepare body scan #42791829407](https://github.com/manufact-test/nomusic/actions/runs/42791829407) **SUCCESS**: no `prepare()V` bodies in those classes or their scanned parent chains. **Do not blindly hook named `ExoPlayerImpl.prepare`**.
- [Existing read-only hooklab #42791829435](https://github.com/manufact-test/nomusic/actions/runs/42791829435) **SUCCESS** module build/synthetic only.
- [Native AArch64 Linux GitHub runner #42792130918](https://github.com/manufact-test/nomusic/actions/runs/42792130918) **SUCCESS probe** but `/dev/kvm` unavailable; **not** usable native ARM Android guest.

Full bounded evidence `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md`. All code only on native hooklab branch. No real Yandex source/decoder/runtime hook proven; no Android CELIKOM APK to install. NO Yandex outreach. Primary device/Test.50 untouched. Next requirement remains a safe real native ARM Android test host, then trackId+edition+generation→decoder pre-prepare witness. Do not repeat stale x86/AМetrica experiments.

---

# CELIKOM Android — НАЧНИ ЗДЕСЬ (10.11.2026, проверенный текущий статус)

**GitHub:** `manufact-test/nomusic`.
**Рабочая ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**Кодовый HEAD, CI SUCCESS:** `18e0d1126187a2c2a26eeb7df7a25de935e19a54`.
**Точный бэкап исходников с рабочим кодом:** `backup/android-native-hook-classloader-verified-20261110`.
Любой более новый HEAD после этого — это документационные изменения; сначала проверить ref.

## 1. Что требует владелец. Не менять без его решения

**Один нативный проигрыватель Яндекс Музыки.** Пользователь входит только в самом Яндексе, пользуется родными плейлистами, радио, паузой, перемоткой и Next. CELIKOM выбирает подтверждённый альтернативный аудиоисточник только если он безопасно связывается с *текущими* trackId + edition + generation до decoder prepare. Иначе оригинал. Никакого второго MediaPlayer, WebView, отдельного fake player, чужих OAuth/Passport токенов или обхода DRM/Play Protect/подписей. Разрешённая модель установки в будущем может использовать **совместимую патченную нативную Яндекс Музыку, как ChromaSync**, но не поверх официальной подписи без осознанной смены установки.

**Яндексу ничего не отправлять**. Идею партнёрского письма владелец категорически отверг. Старый `ANDROID-NATIVE-YANDEX-PARTNER-INQUIRY-2026-11-10.md` — только архив, НЕ отправлять.

**Не трогать:** стабильную эталонную Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`; Яндекс Музыку и локальные загрузки владельца на HONOR 50; Windows, расширение, API, БД, production. Не предлагать владельцу тесты синтетического APK вместо проверки подмены в настоящем Яндексе.

## 2. Фактическая архитектура конкурента

[ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) заявляет native in-process модуль:
- **Без root:** совместимый оригинальный APK + патчер на устройстве + модуль; может требоваться удаление официального Яндекса из-за разных подписей.
- **С root:** LSPosed + модуль внутри Яндекса.
- В публичном Android-репозитории только README. Прямого исходного audio hook нет. Нельзя выдавать README за подтверждённую реализацию или обещать аналогичные результаты.
- Успех конкурента не делает безопасным наш параллельный клон с другим packageId. Именно этот путь уже потерпел неудачу.

Ещё один исходный пример [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) использует modern libxposed `onPackageReady` / classloader для **UI**, не для аудио. Это подтверждает полезность lifecycle-подхода, но не FileInfo->decoder.

## 3. Что реально подтверждено CELIKOM

- **Свой ARMv7 libxposed in-process witness на HONOR:** скрин владельца `Module hook armed=YES`, `onCreate intercepted=YES`, [CI 42643802887](https://github.com/manufact-test/nomusic/actions/runs/42643802887). Это ТОЛЬКО собственное приложение, не Яндекс.
- **Подписанный издателем Яндекс `2026.10.3 #170gpr`** (5 splits, 6 DEX) запускается в чистом изолированном Android 11 x86 с ARM translation. Из его DEX статически найдены `FileInfoApi/OldFileInfoApi @Query("trackId")` как param 0, `sw7.y0/z0(FileInfoDto,boolean):eed`. Реальная текущая edition+generation к конкретному decoder prepare ещё НЕ доказана.
- **Параллельный clone другого packageId**: MAIN `EXIT_SELF status 0`, вспомогательный `:AppMetrica` остаётся. Точная причина самозавершения не определена, **это не доказанный anti-tamper или несоответствие подписи**. См. `ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`.
- **Same-package LSPatch на x86/ARM-translation AVD**: и с модулем, и без модуля раньше падал в загрузчике `liblspatch.so` / `UnsatisfiedLinkError` ДО нашего hook; [42622523007](https://github.com/manufact-test/nomusic/actions/runs/42622523007), [42622723034](https://github.com/manufact-test/nomusic/actions/runs/42622723034). Это не проверка настоящего ARM. **Не повторять эти x86 тесты.** `.github/workflows/android-native-yandex-emulator.yml` переведён на manual-only.
- Уже реализованы *синтетические* `NativePrePrepareAdmission`, `NativeSourceGate`, `NativeTrackIdentityGate`: точные edition/generation/ready/expiry проверки. Ни один из них не включён в настоящий decoder.

## 4. Новый реальный код в этой сессии

`android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeHookEntry.java`:
- После exact-version проверки сохраняет только host Context, а при `onPackageReady` повторно пытается установить **read-only** хуки, если на `Application.attach` split-классы ещё не были готовы.
- Частично установленные хуки не дублируются: `modernHooked`, `legacyHooked`, `accessorHooked`.
- `HookSpec.findConversionPair(preferred, fallback)` требует **обе** точные сигнатуры `sw7.y0/z0` из **одного** classloader. Если preferred loader ещё не готов, пробует validated Context loader. Нет смешивания моделей из двух loader и нет fuzzy fallback.
- `HookSpecTest` проверяет точный version gate, пару, отказ при неподходящем loader и fallback.
- **[CI #42790028152](https://github.com/manufact-test/nomusic/actions/runs/42790028152) SUCCESS 2/2:** Java-policy и Android libxposed module APK build. Это НЕ тест реального Yandex hook. Исходники в `18e0d1126187a2c2a26eeb7df7a25de935e19a54`, отдельный бэкап `backup/android-native-hook-classloader-verified-20261110`.

**Изменений источника звука нет.** Модуль по-прежнему считает конвертации без чтения trackId, URL, ключей, токенов. НЕ продавать это владельцу как работающий Android CELIKOM.

## 5. Точный следующий рубеж

1. Нужна воспроизводимая **гостевая нативная ARM-среда** с совместимым same-package подготовленным Яндексом и без риска для основной установки; отдельный аппарат/разрешённая cloud ARM с допустимой установкой. Старые x86 AVД/clone нельзя выдавать за ARM proof.
2. Только после успешного native MAIN UI/login **в Яндексе**, Play Protect и hook witness: получить read-only runtime связь `current trackId + edition + generation -> FileInfoDto -> фактический source/decoder BEFORE prepare`. Не собирать пользовательские токены или чужие аудиопотоки.
3. Только после такого доказательства связывать `NativePrePrepareAdmission` с реальным нативным входом и затем тестировать «Раскол» `42884423`, «Дым» `39949113`, начало без «пшика», Next, radio, seek/pause. Никаких выдуманных CI green.

**Сейчас** без такого разрешённого native ARM runtime `NO-GO` для установки/теста владельцем; не требовать от него удалить официальный Яндекс и не запускать бесконечные emulator/DEX/AМetrica эксперименты. Если появится настоящий тестовый кандидат, обращаться к владельцу **один раз, только для реальной ручной проверки**, заранее называя риск удаления/подписей.

## 6. Исторические материалы

Старый разросшийся NEXT-CHAT с устаревшими и частично противоречивыми решениями сохранён **только для истории**: `docs/android/ARCHIVE-NEXT-CHAT-ACCUMULATED-20261110.md`.

Контекст: `docs/android/ANDROID-NATIVE-COMPETITOR-PATH-CORRECTION-2026-11-10.md`, `docs/android/ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md`, `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md`. Во всех спорных местах приоритет у настоящего документа и новых подтверждённых результатов CI, не у старых прогнозов.
