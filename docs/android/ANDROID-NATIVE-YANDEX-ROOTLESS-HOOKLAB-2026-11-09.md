# CELIKOM Android · Native Yandex rootless FileInfo hook lab · 2026-11-09

**Текущий статус: подготовленный, успешно собранный и структурно проверенный модифицированный нативный клиент для отдельной тестовой среды. РАБОТА С ЗВУКОМ И PLAY PROTECT НА УСТРОЙСТВЕ ЕЩЁ НЕ ДОКАЗАНА.**

## 1. Контракт владельца и изоляция

Рабочая ветка: `experiment/android-native-yandex-fileinfo-hooklab-20261109`, создана **от** `experiment/android-native-yandex-gate1-20261109` / `c285fc65262d79a731883bea14b23bbb2a076b9b`. Владелец разрешил исследовать и готовить модифицированный **нативный** Яндекс для отдельного тестового устройства, не трогая его HONOR и оригинал.

- Только клиент Яндекс.Музыки `ru.yandex.music` и его настоящий единственный проигрыватель; не WebView, не отдельный MediaPlayer и не браузерная оболочка.
- Пароль/2FA пользователя только в самом Яндексе, никогда в CELIKOM; никаких OAuth-заголовков, токенов и личных файлов в логах.
- Никакого root/отключения Google Play Protect/маскировки под ключ издателя. Важно: обычная бесшовная установка поверх оригинала **невозможна** из-за переподписи APK.
- Продуктовые файлы Android Test.50, текущая основа, сервер, хранилище и каталог треков не менялись.

## 2. Что действительно реализовано и собрано

`android/native-yandex-hooklab/` — **реальный модуль libxposed API 102** (компилируется отдельно). Это пока *чистый read-only наблюдатель* для настоящего native FileInfo converter:

```text
ru.yandex.music 2026.10.3 #170gpr, code 24026531
  native FileInfoApi: resources/v2/file-info
  native OldFileInfoApi: get-file-info
    -> native FileInfoDto (urls, codec, key, bitrate, quality, gain, r128)
       -> sw7.y0(FileInfoDto,boolean): eed
       -> sw7.z0(OldGetFileInfoDto,boolean): eed
          [CELIKOM read-only post-call hooks; original result untouched]
  one original Yandex player; no separate CELIKOM audio decoder
```

- В Android-рефлексии требуется **точное совпадение** package/versionCode/versionName и имен/типов двух методов/возвращаемого типа. На другом клиенте — fail-closed, никакого приблизительного hook-all.
- Оба перехвата выполняют оригинальный метод через `chain.proceed()`, **не меняют аргументы и результат**, считают только успешные вызовы. Лог содержит только `modern/legacy count`, без ID, аудио URL, ключа, metadata и cookie.
- Манифест **не требует ни одного Android permission** (нет INTERNET, Accessibility, storage, microphone).
- Хуки используют защитный `PROTECTIVE` режим; собственная ошибка модуля должна не мешать Яндексу.
- Никаких исходников Яндекса, XAPK, APKS, keystore, песен и личных данных в репозитории.

## 3. Реальные проверки, а не легенды про CI

- [CI #42611563341 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42611563341): Java 17 / Gradle / Android SDK 35 / modern libxposed 102, Android APK собирается и проходит `apksigner`, все `META-INF/xposed` файлы и scope `ru.yandex.music` присутствуют; синтетические тесты точного метода проходят.
- [CI #42613009821 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42613009821): **настоящая** Yandex `#170gpr` из verified XAPK разбита на 5 APK, проверена подлинная исходная подпись; в изолированном runner LSPatch патчит их и встраивает **именно наш** модуль. Все 5 частей имеют единый **одноразовый лабораторный** сертификат; встроенный модуль проверен по SHA-256 и пакет/версия/сплиты совпадают с исходником. **LSPatch `sigbypass=0` — отключено любое spoofing оригинальной подписи**. Java 17 для модуля, Java 21 для LSPatch.
- [CI #42613455742 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42613455742): дополнительный предварительный контроль — в **точной реальной #170gpr** объявлены и содержат код методы `sw7.y0(FileInfoDto,Z):eed` и `sw7.z0(OldGetFileInfoDto,Z):eed`. Имена не просто найдены в текстовых ресурсах — проверена DEX class/method definition.
- Исходный XAPK — **60,433,885 bytes**, SHA256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`, original publisher signer SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`. Патчер [JingMatrix/LSPatch v1.2-487](https://github.com/JingMatrix/LSPatch/releases/tag/v1.2), JAR SHA256 `d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165`. Исследование LSPatch GPLv3; **никакого распространения** перепакованного клиента и лицензионных утверждений о разрешённом релизе.
- Упакованные пять частей: base; `config.armeabi_v7a`, `config.en`, `config.mdpi`, `config.ru`. Native ABI — **armeabi-v7a**.
- CI не сохраняет/не загружает проприетарные APK в artifacts и не предоставляет пользователю APK. Одноразовый signing key удалён с runner; он **не предназначен для обновлений на реальном телефоне**.

## 4. Что остаётся объективно НЕ проверенным

1. **Фактическая загрузка хука внутри процесса** изменённого Яндекса на Android 13 и получение `FileInfoDto` именно при проигрывании. Компиляция и встраивание ≠ выполнение. Для этого подготовлен отдельный автоматический Android 13 emulator job (`android-native-yandex-emulator.yml`), он не использует аккаунт. Не считать успешным до финального статуса CI.
2. Google Play Protect **на реальном, сертифицированном устройстве с защитой ON**. Google Play system image эмулятора не заменяет полноценный device verdict, даже если установка прошла.
3. Совместимость входа в Яндекс без spoofing оригинальной подписи: переподписанный клиент может отклонить Yandex OAuth/Play services/integrity. Любая попытка обходить предупреждения, anti-tamper или Play Protect — **запрещена**. Если отказ — честный блокер, не выкручивать `sigbypass`.
4. Для подмены одного источника: строгое catalog `trackId` + editionId, связь `eed` с тем же native decoder **до prepare**, rights/entitlement, prebuffer/range/seek/duration, fail-open на оригинал. Текущий модуль **не заменяет звук**. Нельзя выдавать его за рабочий CELIKOM.
5. На данном CI/в чате нет отдельного физического ARM-тестового телефона, поэтому **не заявлять**, что реальный звук/пауза/перемотка/радио прошли проверку.

## 5. Следующее действие по техническому результату

Если Android 13 эмулятор подтверждает загрузку точных хуков — исследовать sanitized runtime `FileInfoDto→eed` во время законного тестового трека и обеспечить pre-prepare source ownership, затем писать минимальный одноисточниковый selector с защитами. На отдельном тестовом устройстве с Play Protect ON надо пройти настоящие native play/seek/pause/next, и только тогда передавать владельцу кандидата.

Если эмулятор не поддерживает native ABI или модифицированный клиент не запускается — зафиксировать **точную** причину (устройство/ABI/подпись/отказ без spoof), не переносить эксперименты на HONOR и не возвращаться к WebView/двоеплеерной схеме.

