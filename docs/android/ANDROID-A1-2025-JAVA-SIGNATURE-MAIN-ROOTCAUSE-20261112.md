# CELIKOM Android A1 — уточнение реального Java startup blocker: MAIN IllegalStateException содержит SIGNATURE

**12.11.2026.** Текущая единственная реальная приёмка: **Stage A NO-GO / Stage B LOCKED**. Подписывание, установка и начало запуска доказаны; работа родного UI, авторизация и подмена звука не доказаны.

## Зачем этот блок

Предыдущий каузальный ARM13 опыт [CI 43112641177](https://github.com/manufact-test/nomusic/actions/runs/43112641177) исключил переименование пакета и rebuild APKEditor как обязательные причины Java-краша. Оставался общий `APPLICATION_STATE` без определённой причины. Новая работа сузила категорию **строго по точному MAIN PID** и AndroidRuntime, без публикации чужих stack traces/исключений/токенов.

## Последовательность проверок, только проверенные факты

1. Исходный **publisher-signed** Yandex Music 2025.10.4 #120.1gpr, 16/16 оригинальных split APK, **75 sec native MAIN PASS** [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430).
2. Полная собственная подпись 16/16 для того же издательского материала (minSdk=24) **PASS**, включая реальную Android13 native установку 16/16. [CI 43105227726](https://github.com/manufact-test/nomusic/actions/runs/43105227726) / [CI 43105679694](https://github.com/manufact-test/nomusic/actions/runs/43105679694).
3. Независимо подписанная **копия с оригинальным именем пакета** (без смены Manifest/resources/DEX/native payload, без APKEditor, без LSPatch) **все 16 APK устанавливаются**, `am start` принимает родную MainScreenActivity, затем MAIN падает с `ApplicationExitInfo.JAVA_CRASH status ZERO`. [CI 43112641177](https://github.com/manufact-test/nomusic/actions/runs/43112641177). Бинарь, переданный издателем, не изменяли; только отдельные ephemeral lab-копии.
4. Изолированная безопасная диагностика `clone_main_crash_buffer.py` расширена: начальный/root Java throwable, семейство первого stack frame, точный UI/background thread, allowlisted слово-характеристика первого исключения, fixed security words. Не выводит полные имена сторонних классов и методов, raw message/stack, package paths, URL, PID, account data. Синтетические regression tests **28/28 PASS** [CI 43118152206](https://github.com/manufact-test/nomusic/actions/runs/43118152206); ранее **26/26 PASS** [43117469303](https://github.com/manufact-test/nomusic/actions/runs/43117469303) и **23/23 PASS** [43114504196](https://github.com/manufact-test/nomusic/actions/runs/43114504196).
5. **Новый настоящий ARM13:** [CI 43117532628](https://github.com/manufact-test/nomusic/actions/runs/43117532628) снова signature/install 16/16 PASS, native MAIN FAIL. MAIN-only exception: `ILLEGAL_STATE`; **origin `YANDEX_APP`** (top and root), **no Caused-by** stack, 8 scoped frames. Первый текст исключения дал **`TRUST_OR_PACKAGE`** лексическую категорию. Это **ещё не доказательство** конкретной проверки сертификата.
6. **Самый точный настоящий ARM13:** [CI 43118196605](https://github.com/manufact-test/nomusic/actions/runs/43118196605) — повтор sign/install 16/16 PASS, native UI Main 75s FAIL, `JAVA_CRASH / ILLEGAL_STATE`, **`MAIN_UI`** thread, верхнее исключение на стороне `YANDEX_APP`, **`java_exception_security_markers=["SIGNATURE"]`**: слово «signature» присутствует **в тексте первого IllegalStateException**, а не подхвачено из вспомогательного процесса, пути APK, stackframe или vendor exception type. Обнаружен `java_startup_lifecycle_enum=NOT_OBSERVED`, других `Caused by` нет. Это **сильная новая улика для гипотезы о подписной совместимости/проверке доверия**, но **не доказательство**, что выполняется именно намеренная локальная self-signature-защита: сообщение может относиться к иному подписному контракту. Нельзя подставлять в отчёт неполученные сообщения/классы. Real CI expected FAIL.

## Что означает результат

**Доказано:** проблема уже НЕ в `apksigner`, уже НЕ в PackageManager установке, уже НЕ исключительно в переименовании пакета или APKEditor. Яндекс сам выбрасывает `IllegalStateException` в UI-потоке с буквальным словом `signature` в сообщении, когда *сохранено исходное имя* и *заменён сертификат на собственный*. Тест очень сильно указывает на publisher-signing compatibility / signature-dependent invariant, но конкретный внутренний механизм и возможность альтернативной безобходной интеграции ещё неизвестны.

В частности, невозможно честно сообщить «осталось только поставить APK на телефон» или «падение исправлено». Никакого consumer/user APK, авторизации и аудиоподмены Stage A пока не создано.

## Решение владельца и рамки работы

Владелец **категорически и неоднократно запретил предлагать обращаться к Яндексу за разрешением**. Его дальнейшие сообщения не должны тратить время на эту дискуссию. Продолжить техническое исследование, не переделывать уже работающие 16 подписи/установку.

Действующая архитектура/сохранённый мастер фиксирует отсутствие signature spoof/Play Protect/DRM/Passport обходов, смены Яндекс-плеера, WebView, стороннего кода конкурента. Не выдавать экспериментально неподтверждённую сборку и не менять договорённые архитектурные ограничения молча. Правовой статус коммерческой дистрибуции неизвестен, владелец не поручал получать разрешение.

Для следующего технического исследования вместо повторного подписания — проверять независимое сохранение publisher-signed исходного runtime (без модификации чужих APK), поддерживаемые нативные hooks в собственной среде, либо возможный системный **signature-level permission dependency**, сохраняя ограничения. Отсутствие полученного нативного запускa надо считать текущим blocker, а не поводом переключаться на WebView/свой decoder.

**Точная непрерывность:** main A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743` не трогали. Test.50, Windows, extension, production API/backend, админка, HONOR, официальный Яндекс и неопубликованный оригинальный Release нетронуты. Test archive SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45 961 661 байт, 16 splits — использовать существующий draft, ни в коем случае не публиковать чужой binary или signing keys.

**Рабочий источник:** `experiment/android-a1-2025-causal-startup-controls-20261112` — реальные ARM13 тесты. Дополнительные 28 диагностических regression tests в отдельной ветке `experiment/android-a1-2025-privatelog-java-rootcause-20261112` (её результаты синтетические); код безопасного классификатора в обеих ветках синхронизирован.
