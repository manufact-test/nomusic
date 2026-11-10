# CELIKOM Android A1 — реальный ARM LSPatch runtime witness (11.11.2026)

**Ветка:** `feature/android-native-clone-lspatch-a1-20261111`
**База/резерв:** `a20abb68316ea20266fb98139bb78675bf0beb97` / `backup/android-native-clone-a0-before-implementation-20261111`.

Главное ТЗ: `CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md`. Этот checkpoint не изменяет архитектуру и не заменяет продукт собственным плеером.

## Проверенное состояние перед A1

- В `android/native-yandex-hooklab` имеется **read-only** LibXposed module с точным #170gpr `FileInfo` + `Lero/Lemb` observer; **никакой подмены байтов**.
- Архивные LSPatch-прогоны на Android 11 x86/x86_64 translated host завершаются до загрузки CELIKOM модуля. ARM phone runtime **ещё не проверялся**; универсального NO-GO нет.
- Исходный #170gpr комплект содержит **пять split APK**. Отдельная package-name clone архитектура ранее дала `EXIT_SELF(0)`/конфликт владельца custom permission; **нельзя объявить, что свой package name + один universal APK уже работают**.
- Windows accepted W61 и Android Test.50 сохраняются; для Android НЕ переносим их вторую аудиосистему.
- Файл `ChromaSync-Clone-3.0.1.apk` обнаружен в Library `/CELIKOM/`, но raw bytes для приватного анализа в данном контексте недоступны. Содержимое APK **не проверялось**, код конкурента не переносился.

## Реализовано в A1

`witness_installed_arm_host.py` — **НЕ сборщик и НЕ установщик**. Это ограниченный read-only свидетель действительного **in-process вызова** собственного модуля на отдельно разрешённом ARM Android 13+ со штатно включённым Play Protect. В отличие от виртуальных тестов он работает только с реальным приложением на тестовом телефоне:
1. Требует явного подтверждения *запасного*, не основного HONOR, телефона и Play Protect.
2. Повторно использует строгий `probe_arm_device`, но уже для **установленного на запасном телефоне** lab host; отказывает владельческому HONOR, x86, Android < 13, без ARMv7 ABI/Play Store и отсутствующему host.
3. Проверяет установленный `ru.yandex.music` *versionCode=24026531*. Не притворяется, что это проверка подписи.
4. Пассивно наблюдает `CELIKOM-NativeLab` logcat, **только whitelisted счётчики/категории**, без печати/сохранения самих логов и секретов.
5. Не перезапускает приложение, не ставит APK, не читает аккаунт/аудио и не изменяет штатный Яндекс. Только живой witness, **не аудио-подмена**.

### Запуск — только ПОСЛЕ отдельной разрешённой установки A1 на запасном телефоне

```bash
python3 android/native-yandex-hooklab/witness_installed_arm_host.py \
    --confirm-disposable-arm-device --confirm-play-protect-on --seconds 60
```

Во время окна пользователь сам слушает тестовый трек, делает pause/seek/Next. Скрипт не загружает и не передаёт содержимое песен. Результат JSON *не* является свидетельством акустического успеха и не устанавливает точную пару current track+edition+decoder.

### Следующие честные gates

1. Доступ к отдельному native ARM Android 13+ с 32-битным ARM ABI; не использовать основной HONOR.
2. Безопасный приватный native LSPatch A1 host, **без sigbypass и любых Play Protect обходов**, допустимый для установки. При hard block — STOP.
3. Свидетель реального входа модуля и lifecycle на устройстве, затем привязка **точно выбранного** native decoder/preprepare к trackId+edition+generation.
4. Только после этого — одобренный stream из CELIKOM API в одном штатном декодере и реальные pause/seek/Next/MyWave акустические проверки. Без них **NO-GO к рабочему APK**.

**Важно:** исходная rootless LSPatch сборка на тестовом телефоне может иметь `ru.yandex.music` и конфликтовать по подписи с официальным приложением. Стадия A1 не доказывает отдельную установку с `pro.celikom.*`. Пользовательский один APK, CELIKOM аккаунт/trial, Play Protect и постоянная подпись остаются не пройденными релизными критериями.

**Обязательная будущая точка:** после подтверждённого владельцем полного акустического LSPatch-эталона сохранить exact source/APK/SHA и **самостоятельно предложить этап B: собственный механизм вместо LSPatch**.


## Добавление A1: локальный приватный результат патчера

Ранее `ephemeral_patch_lab.py` полностью удалял готовые исследовательские split APK после CI. Теперь **после всех существующих проверок** есть *опциональная* локальная выгрузка пяти lab-подписанных split APK во **вновь создаваемую папку вне Git**. В GitHub Actions экспорт полностью запрещён, никакой APK не коммитится, не загружается в artifacts и не устанавливается автоматически. Рядом с файлами создаётся `research-receipt.json` с SHA256 каждого split, lab signer и честным статусом. Ключ экспериментальной подписи временный и удаляется после создания — это не путь обновления клиентского APK.

Чтобы включить *только на собственном изолированном компьютере* (после решения по запасному ARM устройству), собрать модуль `gradle -p android/native-yandex-hooklab :app:assembleDebug` и выполнить:

```bash
export CELIKOM_ARM_LAB_OUTPUT_DIR="/absolute/path/new-private-arm-lab-output"
export CELIKOM_ARM_LAB_EXPORT_ACK="I_CONFIRM_PRIVATE_ARM_SPARE_RESEARCH_ONLY"
python3 android/native-yandex-hooklab/ephemeral_patch_lab.py
```

Выход **не соответствует финальному требованию «один APK CELIKOM с собственным package name»**: это исследовательские пять split APK `ru.yandex.music` для отдельной чистой среды. Нельзя ставить поверх официальной Яндекс.Музыки с другой подписью и нельзя считать пробу допуска Play Protect успешной без реального теста. Производственная установка и выдача пользователям запрещены до дальнейшей проверки.
