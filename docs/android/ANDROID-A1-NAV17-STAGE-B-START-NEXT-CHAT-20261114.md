# CELIKOM Android A1 — точная передача следующему ведущему, 14.11.2026

## 1. Главное: реальный успех, который нельзя потерять

**NAV17 — первая подтверждённая владельцем рабочая сборка Android A1.** На настоящем HONOR 50 (Android 13) открылся **настоящий интерфейс Яндекс.Музыки внутри одного APK CELIKOM**, пользователь увидел собственные альбомы и «Мою волну», **лично подтвердил воспроизведение оригинальных треков**. Это не эмуляция и не только успех CI.

Файл владельца `CELIKOM-A1-Diagnostics-1794687390507.txt` (сохранён в Library: `/CELIKOM/CELIKOM-A1-NAV17-Owner-Real-Music-Success-Diagnostics-1794687390507.txt`) содержит свежую секцию `DIAGNOSTIC_BUILD=NAV_V17_PASSPORT_PROVIDER_AUTHORITY_FIX` с подтверждённой цепочкой:
- `LOGIN_PIPELINE_SOURCE=AUTOLOGIN_UID_RESULT`
- `LOGIN_TOKEN_OUTCOME=WRAPPED_STRING`
- `LOGIN_PIPELINE_RESULT=USERINFO_READY` (`AFTER_SYNC`)
- `LOGIN_FLOW_RESULT=USERINFO_READY`
- `POSTLOGIN_PUBLISH=REAL_USERINFO_SUCCESS`
- `POSTLOGIN_MAIN_ROUTE=MAIN_REQUESTED`
- `MAIN_ACTIVITY=CREATED/STARTED/RESUMED`, затем `VENDOR_ACTIVITY=CREATED/STARTED/RESUMED`.

**Но версии треков CELIKOM НЕ подменяются.** Внутри работает исходная Яндекс.Музыка и играет исходный звук. Нативная авторизация/плеер — пройденный этап A; продукт CELIKOM до выпуска **не готов**. Этап B — подключить подмену источника в том же штатном плеере.

## 2. Точная база, откат и подпись

GitHub `manufact-test/nomusic`; **единственная рабочая ветка Android A1**:
`experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

Перед подтверждением NAV17 HEAD исходного кода `d4c0887028b2bfbad7ed59f63ec88a4770f3595d`.

**Неприкосновенный эталон и точный резерв, уже создан и проверен:**
`backup/android-a1-nav17-owner-real-userinfo-main-music-audible-20261114` → `d4c0887028b2bfbad7ed59f63ec88a4770f3595d`.

**APK, которую владелец реально поставил и на которой Музыка играет:**
Library `/CELIKOM/CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`.
SHA256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`.
Постоянный сертификат подписи SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
Оригинальный встроенный пакет Яндекса SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`.

**Не трогать сохранённый эталон**, не переустанавливать с удалением данных, не менять ключ подписи, не менять оригинальную Яндекс.Музыку, не трогать Windows/`main`, не вводить новую тестовую линию Android. После существенных изменений делать свой точный резерв с возможностью отката.

**Что именно починило вход:** NAV17 восстановил в клоне три собственных `ContentProvider` authority Яндекс Паспорта по формуле, которую оригинальный SDK собирает из `Context.getPackageName()`. В NAV16 их ошибочно заменяли хешами, из-за чего штатный запрос токена завершался `PASSPORT_API_UPPER_A`. Реальная проверка NAV17 на телефоне подтверждает успешный запрос токена и UserInfo. Не возвращаться к старым теориям AppMetrica/Passport и не трогать этот участок без новых доказательств.

## 3. Точное оставшееся препятствие: только аудиоподмена

На рабочей ветке:
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java` содержит **наблюдение** `MediaDataSource.readAt` и `MediaExtractor.setDataSource(MediaDataSource)`, но не выполняет CELIKOM resolve и не заменяет источник звука.
- `android/native-yandex-hooklab/ci/a1_private_2025_audio_entrypoints.py` — read-only точный DEX-анализ оригинального Yandex player. Исторический документ `docs/android/ANDROID-A1-2025-MEDIADATASOURCE-READAT-HANDOFF-20261113.md` описывает путь source/decoder; наличие observer не доказывает реальное применение замены.
- `android/native-audio-contract/source-contract.mjs` + тесты — ранее подготовленный fail-closed контракт выбора источника. Это **отдельная модель**, а не подключённая функция native Android. Не выдавать тестовый PASS за замену музыки.
- `server/src/Application/ResolveService.php`, `server/src/Http/AudioController.php`, `android/native-audio-contract/server-byte-range-compat.test.mjs` — существующий каталог, авторизация доступа и серверный HTTP ByteRange. Не подменять права, entitlement, approval, версию, SID или signed URL самодельными значениями.

Следующему разработчику действовать **крупными автономными блоками**, без остановок и отчётов на каждом микрошаге:

1. Зафиксировать из уже известной ветки самый ранний реальный native source-before-decoder стык, точно привязать к текущей песне идентификаторы Yandex **track ID + album + edition + duration** и реальный текущий source instance. Без title/artist угадывания; в старом TXT hot-path `MEDIA_DS_READ` намеренно не пишется в выгружаемый TXT.
2. Подключить безопасный запрос к CELIKOM: только подтверждённые точная версия/права/entitlement и валидный подписанный URL, expiry, MIME, Range/HEAD; при недостатке доказательств всегда **оригинальный звук**, никаких ложных замен.
3. Реализовать подмену **в рамках одного штатного Yandex player, до декодера**, сохранив паузу, перемотку, Next, «Мою волну», правильный альбом/версию, полный трек и fallback. Не создавать второй проигрыватель, не подменять UserInfo или токены, не ломать native UI.
4. Проверить isolated tests и оба реальных CI-пути Android 13 (clone-only, original-Yandex-first side-by-side) без подавления ошибок; обеспечить прежнюю подпись и неизменность оригинала. Только после работающего source integration собирать **одну настоящую подписанную APK** для владельца, автоматически выгрузить в Library и дать прямую ссылку. Не просить владельца нажимать Actions, переустанавливать начисто или снова проходить Яндекс ID ради диагностики.
5. На устройстве владелец проверяет одну реально подменённую песню и одну без замены, Start/Stop, Next/«Мою волну», pause/resume/seek и правильный fallback. **До этой проверки не заявлять, что CELIKOM Android готов к выпуску.**

## 4. Как общаться с владельцем

Писать **по-русски, по-мужски, кратко, без корпоративного тона**. Владелец хочет, чтобы разработчик **сам делал работу до момента действительно нужной ручной проверки**, крупными блоками; не заставлять его кликать Run workflow, разбирать лог, авторизоваться снова или устанавливать десятки диагностик. Не показывать промежуточную кухню без причины. Не путать этап A (уже работает) с этапом B (наши версии ещё не играют).

**Первое действие следующего чата:** прочитать этот файл, `docs/android/ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md` и `docs/android/NEXT-CHAT-ANDROID-A1-LEAD-20261113.md`, проверить HEAD и backup, продолжить audio-source integration. В последнем огромном NEXT-CHAT много исторических `Stage B LOCKED`: они отменены подтверждённой владельцем NAV17; теперь Stage B разрешено **разрабатывать**, но выпуск ещё NO-GO.
