# CELIKOM Android A1 — независимый пакет 2025 на ARM13, 12.11.2026

**Главное:** проверен настоящий нативный запуск отдельно подписанного Яндекс-хоста с оригинальным именем пакета в LSPatch2, но отдельно именованный CELIKOM ещё не стабилен. Выпущенной пользовательской APK нет.

## Принятый положительный результат

[Реальный контроль на Android13 ARM64+ARMv7, CI #43190701118](https://github.com/manufact-test/nomusic/actions/runs/43190701118): оригинальные 16 издательски подписанных 2025.10.4 #120.1gpr verified; издательский base подан непосредственно на вход upstream LSPatch; **level0** — crash Java IllegalStateException с маркером SIGNATURE, **level2** — тот же процесс native MAIN стабилен 25/25, Activity resumed 25/25 на протяжении 75 секунд. У обоих вариантов собственная и одинаковая лабораторная подпись, 15 остальных splits пересобраны без изменения обычного содержимого. Вложенных музыкальных модулей нет. Изолированная ветка и точный резерв: `experiment/android-a1-2025-publisherbase-lv0-lv2-arm13-20261112` / `backup/android-a1-2025-publisherbase-lspatch-level2-native75s-pass-20261112` @ `8bdfb55c8c3496212800a8b40d3862076fea67f2`.

## Новый независимый пакет

Отдельная экспериментальная ветка `experiment/android-a1-2025-lv2-own-package-parallel-20261112` использует собственный пакет `pro.celikom.yandex.nativeclonelab` и существующий неизменённый оригинальный 2025 XAPK из закрытого GitHub draft. Отдельная лабораторная сборка прошла все 16 split signature/install checks; LSPatch2 config содержит только проверенные метаданные исходной издательской подписи, без стороннего модуля.

Последняя воспроизведённая проверка [ARM13 #43194694073](https://github.com/manufact-test/nomusic/actions/runs/43194694073), CI job SUCCESS в смысле выполнения скрипта, **но выдаёт NO-GO для продукта**:
- Собственный отдельно именованный APK **INSTALLED**, его native Activity стартует, но MAIN не стабилен: PID присутствует 4/25 срезов, Activity resumed 1/25; `JAVA_CRASH` / `IllegalStateException` из Yandex app в **НЕ main thread**, без `SIGNATURE` marker. Это иной сбой, не доказано, что его исправляет дальнейшая настройка подписей.
- Затем установка подлинных publisher original 16 splits рядом с независимым пакетом отвергнута **`INSTALL_FAILED_DUPLICATE_PERMISSION`**. В репозитории уже имеется отдельное старое исследование причин глобального конфликта одноимённых Android manifest `permission` declarations; оно не имеет отношения к источнику аудио.
- Подлинный signed оригинал на телефон пользователя не ставили/не удаляли; лабораторные APK, временные signing keys и Android guest в CI уничтожены.
- LSPatch origin nested ZIP исправлялся существующим `recover_stored_origin_crc.py`; upstream public APKEditor 1.4.9 получен с проверенными size/SHA через GitHub; нет необходимости повторять проблемы download/ZIP.
- **Нет** проверки живой авторизации, Моя волна, пауза/seek/Next, native pre-prepare source select, акустического звучания или Play Protect на HONOR.

## Приоритетные дальнейшие проверки

Сначала отдельно устранить подтверждённый PackageManager конфликт объявлений одноимённых publisher custom permissions, не расширяя фактические права нашего APK, и выяснить причину отдельного NON_MAIN IllegalStateException, не принимая его ошибочно за старую MAIN SIGNATURE. После фактической стабильности отдельно именованного нативного приложения проверить установку оригинала рядом, затем вход, полноценные экраны и единственный родной декодер, и только затем реальный B42 source-choice и звук. Стабильный сам по себе подписанный Yandex host с исходным package `ru.yandex.music` нельзя выдавать как отдельно устанавливаемый CELIKOM.

Владелец явно пересмотрел старую добровольную инженерную настройку избегать LSPatch signature compatibility; это не отменяет осторожности с доверенными приложениями, а также обязательной проверки пользовательских функций. **Stage A NO-GO, Stage B LOCKED.**

Frozen main A1 `cc4cb0f93489168db21502f3ef195855ae9fb743`, Test.50, Windows, extension, PHP/backend, production и HONOR не менялись.
