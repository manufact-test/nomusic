# CELIKOM Android A1 — финальный инженерный заход, 12 ноября 2026

**Статус продукта: Stage A NO-GO. Stage B LOCKED. Пользовательского CELIKOM Android APK с работающим Яндексом пока нет.**

Этот отчёт актуальнее более ранних исследований; **утверждённую архитектуру не пересматриваем**. Один отдельно устанавливаемый CELIKOM APK, настоящие нативные экраны/авторизация/Моя волна/плейлисты Яндекса, штатный **единственный** декодер, CELIKOM только выбирает разрешённый альтернативный источник для указанного трека. Официальная Яндекс.Музыка должна остаться отдельно на HONOR, никаких WebView/вторых игроков. Владелец **окончательно попросил не предлагать обращения к Яндексу за разрешением**. Не возвращаться к вопросу без нового запроса владельца.

## 1. Реально доказанная последняя проблема

Сертификат и PackageManager теперь не являются проблемой *установки*, но под чужим independently signed certificate нативный Яндекс MAIN не живёт.

- Подлинный publisher-signed Yandex Music **2025.10.4 #120.1gpr** (16 split APK) на настоящем ARM64+ARMv7 Android 13, **тот же самый чистый Redroid guest**, живёт 25/25 проверок за 75 секунд. <https://github.com/manufact-test/nomusic/actions/runs/43171090649>.
- Своим новым сертификатом подписали и проверили 16/16 APK того же `ru.yandex.music`; **все установлены**, MainScreenActivity `am start` принимается, но UI MAIN падает `JAVA_CRASH / IllegalStateException`. PID-scoped classifier видит `MAIN_UI`, `YANDEX_APP` и **слово `SIGNATURE` в первом Java exception message**. Ни смены имени пакета, ни APKEditor, ни LSPatch в этом A/B нет.
- Дополнительный ZIP-audit обнаружил `stamp-cert-sha256` в оригинале; при самостоятельном подписании его нельзя просто считать совпадающим. <https://github.com/manufact-test/nomusic/actions/runs/43172112962>.
- Чтобы не гадать об отсутствующем метаданном, сделали **собственный, честно подписанный и cryptographically verified SourceStamp** отдельным собственным ключом через проверенный **Google SDK 35**: 16/16 source stamps PASS; все **8 661** не-подписных APK entries (включая DEX, .so, manifest, resources) сверены по распакованному SHA256 byte-for-byte; Android install 16/16 PASS. **MAIN всё равно падает с тем же SIG-related IllegalStateException**. <https://github.com/manufact-test/nomusic/actions/runs/43173312016>.
- Даже несуществующую на данном госте гипотезу `signature permission missing` проверили честно: стандартный Android PackageManager после обоих последовательных вариантов выдаёт **30 vs 30 запрошенных**, **15 vs 15 granted**, 0 недостающих grants; `com.yandex.permission.READ_CREDENTIALS` в этом guest отображён GRANTED с обеих сторон. При этом own-key variant продолжает падать. <https://github.com/manufact-test/nomusic/actions/runs/43174180541>.
- Следовательно, **свободное переименование пакета, перепаковка, повторная apksigner, добавление собственного SourceStamp или предоставление уже совпадающих прав не решают старт**. Остаётся различие издательского подписного доверия/обработки пакета/внутреннего состояния, но **конкретная проверка не доказана**. Не утверждать, что найден её адрес/код, не обещать APK завтра.

**Что нельзя повторять следующему чату:** смену ZIP-компрессора и APKEditor без нового основания, перепроверку уже подписанных 16/16 и устанавливаемых 16/16, SourceStamp «ещё раз», ещё один одинаковый ARM13 NO-GO запуск ради самого запуска. Предыдущие реальные A/B исчерпали эти переменные. Не пытаться обходить подписной trust/security, чужой Passport/DRM, Play Protect или использовать private код конкурента как CELIKOM. Не выдавать неподтверждённый APK владельцу.

## 2. Последний полезный кодовой блок — подготовленная наша аудиологика B42

Поскольку не было проверенного native Yandex execution host, **не изобретали фиктивный адаптер к чужому декодеру**. Вместо этого укрепили уже интегрированный в frozen main **наш** подготовленный source-choice contract из issue #42 / PR #43:

- `android/native-audio-contract/source-contract.mjs`: `editionId` из нативного host snapshot теперь принимается только **как строгая непустая строка** без управляющих символов, без неявного `String(object)`/Java object `toString()`. Некорректная edition identity отбрасывается, штатный source не трогается.
- `validateGrant()` больше не принимает `durationMs=0` (или отрицательную длительность) даже если исходный трек очень короткий и укладывается в tolerance. Это реальная граница корректности подмены аудио.
- Два новых детерминированных регрессионных теста: нулевая/отрицательная длительность и некорректные editionId, включая объект с побочным `toString()`, числовые/boolean и управляющие символы.
- Реальный GitHub CI **34/34 PASS**: <https://github.com/manufact-test/nomusic/actions/runs/43176180946>. Это исключительно **наш source-only JS**, **не** настоящий Yandex host runtime, **не** услышанная подмена и **не** разрешение Stage A.

Контракт сохраняет: точный `trackId+albumId+editionId+generation`, права/entitlement из отдельного доверенного адаптера, проверенный signed HTTPS HMAC URL, HEAD/Range, отмена устаревших запросов Next/Моя волна, fallback к оригиналу, отсутствие второго плеера. **Важный будущий blocker:** PHP resolve пока не даёт authoritative album/edition attestation; при неизвестной edition/album — выбирается оригинал, а не выдумываются данные. Живая интеграция к single Yandex decoder **НЕ** установлена.

## 3. Состояние веток и правило передачи

- **Неизменяемая принятая главная A1:** `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`. Не cherry-pick туда непроверенный runtime.
- **Последний доказательный ARM13 backup (до текущего блока):** `backup/android-a1-2025-honest-ownstamp-all8661-grants15-signature-nogo-20261112` @ `fbff3df6e7dc57d9af28053f220e8481a051b5a0`.
- **Текущая финальная рабочая ветка:** `experiment/android-a1-final-native-source-hardening-handoff-20261112`. Её точный финальный SHA и отдельный backup — в `docs/android/NEXT-CHAT-ANDROID-A1-FINAL-20261112.md` / GitHub issue #41.
- **Точная исходная 2025:** unpublished draft GitHub release `a1-yandex-2025-gpr-private-test` (release 442137464, asset 736739728), 45 961 661 байт, SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`. Не просить перезагрузить, не публиковать сторонний APK или ключи.
- **Проверяемые документы:** `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md` (архитектура), `docs/android/ANDROID-A1-2025-PAIRED-OWN-STAMP-AND-SIGNATURE-ROOT-20261112.md`, `docs/android/CELIKOM-A1-2025-SIGNER-TRUST-GATE-20261112.json`, исходный `docs/android/ANDROID-A1-PARALLEL-AUDIO-CONTRACT-20261111.md`.
- **GitHub issue #41 — OPEN.** Issue #42 и PR #43 уже были подготовлены и приняты, не переделывать.
- Эталон Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`, Windows, Chrome-extension, API/backend, БД/production, admin, HONOR, установленный официальный Яндекс — **не затронуты**.

## 4. Самый полезный следующий самостоятельный шаг

**Остановить цикл `подписали→установили→Java SIGNATURE crash`.** Следующий разработчик должен определить _новое_ проверяемое инженерное условие, которое действительно даст нашему отдельно подписанному приложению **свой законный in-process runtime с нативным Яндекс-плеером** либо иную документированную поверхность native source-before-prepare; не повторять доказанный NO-GO. Если такой host не установлен, **не начинать** Stage B и **не давать** владельцу технический APK, не превращать source-only PASS в полноценную сборку.

После возникновения реальной host-точки: доказать ту же нативную UI/логин/MyWave с одним декодером, связать source-choice контракт с `trackId/albumId/editionId` и авторизованным аудио до `prepare`, затем автоматические pause/seek/Next/MyWave/Stop/Range/откаты и владельцу **одну работающую, безопасно отдельно устанавливаемую** APK на HONOR для акустической приёмки. Только после пользовательского реального одобрения Stage A замораживается, а Stage B согласуется отдельно.

**Владелец требует больших самостоятельных блоков, без остановок и отчётов после каждого CI/коммита.** Обращаться к нему только при реально необходимой ручной проверке. Не предлагать просить разрешения у Яндекса — это окончательное пожелание владельца.
