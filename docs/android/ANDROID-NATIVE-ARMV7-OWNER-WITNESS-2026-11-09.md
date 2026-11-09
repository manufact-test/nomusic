# CELIKOM Android — владелец проверил ARMv7 на HONOR, 9 ноября 2026

## Факт от владельца

На HONOR 50, Android 13, успешно установлено отдельное собственное приложение CELIKOM ARM Loader Lab (pro.celikom.armv7loaderhost). Скриншот владельца Screenshot_20261109_180948.jpg: на экране заголовок CELIKOM ARMv7 loader test и сообщение If visible: the 32-bit host activity launched. Владелец сообщил, что установка Google Play / Play Protect прошла без предупреждений.

**PASS:** приложение с собственной ARMv7 JNI-библиотекой запустилось на реальном аппарате; официальная Яндекс.Музыка, её загрузки и настройки не затронуты.

**НЕ доказано:** регистрация Xposed-хуков; в первой сборке не было Xposed-модулей; состояние Play Protect ON не подтверждено независимой проверкой; родная Яндекс.Музыка и подмена аудио не тестировались.

## Подготовлен следующий безопасный эксперимент

Изолированная версия с новым package ID pro.celikom.armv7loaderhost.witness. Отдельный libxposed-модуль pro.celikom.armv7witnessmodule имеет scope только на own-test host. Его метод Application.attach -> MainActivity.onCreate устанавливает два флага в оперативной памяти без разрешений и логов. На экране появятся: Module hook armed: YES / NOT OBSERVED; onCreate intercepted: YES / NOT OBSERVED.

Новый пакет не обновляет и не удаляет ни официальный ru.yandex.music, ни предыдущий ARM Loader Lab. LSPatch -l 0, без root/подмены подписи Яндекса. Проверка не заменяет аудио и не открывает Яндекс.

Source: android/native-yandex-hooklab/armv7-witness-module/; packaging: android/native-yandex-hooklab/build_owned_loader_host.py (CELIKOM_OWN_WITNESS=1); CI .github/workflows/android-native-armv7-hook-witness.yml.

Только после CI SUCCESS и проверки владельцем на HONOR можно утверждать, что LSPatch действительно выполнил собственный libxposed hook в ARM-процессе. Если приложение открывается с NOT OBSERVED — модуль/attach всё ещё не подтверждён. Play Protect не выключать, доступы не выдавать, оригинальный Яндекс не удалять.

Ни на одном этапе этого теста не создан рабочий Android CELIKOM для подмены музыки.
