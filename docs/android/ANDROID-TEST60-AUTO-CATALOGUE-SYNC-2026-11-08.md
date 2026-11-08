# CELIKOM Android — автоматическое обновление каталога одобренных замен

**Дата:** 2026-11-08. **Состояние:** разработано и протестировано в изолированной ветке, подписанная Test.60 готова; **не опубликовано на новом сервере и не проверено на телефоне**. Это не исправление проблем Pause/Seek RASKOL/«Дым».

## Требование владельца
После загрузки и одобрения ещё 100 или 1000 песен владельцу **не нужно писать разработчику, обновлять список вручную или собирать новый APK**. Каталог должен синхронизироваться с сервером. Именно после одобрения модератором, а не после незавершённой загрузки. Никаких дополнительных Android разрешений. Работа музыки и принятый Test.50 fade/seek decoder должны остаться неизменными.

## Почему Test.59 недостаточно
Test.59 встроила **119/119 одобренных песен** из SQL на этапе подписи APK (вместо старых 12), поэтому аварийно починила случай «Мне нужна любовь» при API Яндекс HTTP 451. Но `assets/catalog-diagnostic.json` в APK **статический**: при следующем одобрении новых песен он не меняется сам. Возвращаться к «собери мне новую APK ради каталога» недопустимо.

## Что добавлено
Ветка `feature/android-auto-catalogue-sync-20261108`, основана **прямо на Test.59** compiled commit `64c43d967df662094f3f53e477e168b8e8e40b2a` (Test.59 runtime audio от owner-accepted Test.50 SHA `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`). Test.60 compiled commit `6951504b3eb04e0f77338295a4258e0a9cdf5e79`.

**Backend:**
- `GET /api/v1/replacement-catalog` — JSON metadata-only, **только авторизованным** пользователям с проверенной bearer-сессией; не требует оплаченной подписки и не выдаёт воспроизводимое аудио, приватные файлы, ключи, URL, токены, данные загрузчиков.
- `server/src/Application/ReplacementCatalogueService.php`: каждый GET читает текущие `tracks` и `track_replacements` через **SELECT**. Включены только service=`yandex`, active=`1`, status=`approved`, disabled_at=`NULL`. `EXISTS` убирает дубликаты при нескольких версиях одного трека; список меняется сразу после нового одобрения/отключения. Объём ограничен `MAX_ROWS=5000`; при переполнении сервер не отдаёт частичный снимок.
- Формат совместим с текущим `HybridIdentity.own`: `schema=1,source=celikom_owner_catalog_snapshot,complete=true,generated_at_ms,total_tracks,tracks[{track_id,title,artist,album,duration_ms,replacement_available:true}]`.
- `server/src/Application.php`: отдельный route с auth, только GET, `Cache-Control:private,no-store`. Нет нового секрета и нет публикации на Hostinger.

**Android:**
- `NativeApi.java`: запрос `replacement-catalog` с прежней авторизацией на **отдельном worker-е**; токен обновляется через существующий сериализованный auth-worker; 2 МБ max response и привязка к текущему `accountGeneration`. Не блокирует аудио/resolve/download.
- `LiveCatalogueStore.java` (новый): проверка schema/source/complete/rows/unique ids/duration/approval/time, ограничение 5000 строк/2MB; надёжная запись в приватную app storage через временный файл и rename; invalid/partial/stale ответ не заменяет хорошую копию.
- `AlbumProbe.java`: при старте использует последнюю актуальную сохранённую копию, иначе статический APK backup. Пока сервис активен и пользователь вошёл, проверяет сервер **примерно каждые 15 минут** (повтор через 2 минуты при сетевой ошибке). Если приложение закрыто, проверит после следующего запуска. Новые approved songs доступны без новой APK; не меняет текущий декодер во время слышимой замены.
- `ProbeService.java`: запускает неблокирующую проверку в уже существующем sample loop; нет новых разрешений/второго Media3 controller/изменения Player.
- Всё ещё есть неизменная проверка `AlbumMatch` + продолжительности + server `resolve`; совпадение из каталога **не выдаёт** доступ к аудио без авторизации.

**Тесты и safety:**
- `server/tests/replacement-catalogue.php`: SQLite unit, подтверждены немедленное появление новой одобренной песни и исчезновение отключённой, отсутствие pending/Spotify/duplicates/private metadata. Test PASS.
- `android/native-companion/addon/TestLiveCatalogueStore.java`: 13 host checks — обновление кэша без APK, отказ stale/truncated/duplicate/unapproved/oversize snapshots. Test PASS.
- `android/native-companion/tests/check_test_app_build_contract.py`: требование реального auth endpoint, live refresh, atomic cache; регрессии звука из Test.59 сохраняются.
- [GitHub Actions run 42463932575](https://github.com/manufact-test/nomusic/actions/runs/42463932575): `native-android=success`, `build-test-app=success`, APK подписана original certificate. Stable package и OTA не изменены.
- `0.3.85-test.60/code86146`, signed APK `CELIKOM-Android-0.3.85-TEST-60-LIVE-CATALOGUE-SYNC-SIGNED.apk`, SHA256 `f01a394713c44d9e30d283e3f23379a6c278f6ecae952d073e4d6ee7cf450deb`, 8 841 369 B, app `pro.celikom.nativeprobe.test` (только тестовый отдельный пакет).
- **Library APK:** https://chatgpt.com/library?file_id=libfile_19f6a9a8c9088191bfa1b194077043ee&account_id=personal
- Test verification file `libfile_cabc95eeb4f08191aab8426dba0f7529`, CI receipt `libfile_f3b1e7ae5ea881919557d8c95895ee04`.

## Важно перед проверкой / переездом на MCP
**Это двухсторонняя функция.** Test.60 Android уже умеет обновлять, но текущий живой backend Hostinger НЕ содержит новый endpoint: **не обещать, что Test.60 уже синхронизируется на телефоне**. На новой платформе сначала перенести и применить изменения `server/src/Application.php` и `server/src/Application/ReplacementCatalogueService.php` из ветки `feature/android-auto-catalogue-sync-20261108`, затем подтвердить авторизованный GET: 200, актуальный total, моментальное появление новой approved и исчезновение revoked, 401 для неавторизованного. После этого устанавливать/проверять Test.60. На старом сервере и в main runtime backend никаких изменений не делали.
- Провести **один** сквозной E2E: модератор одобрил тестовую песню в новой БД -> API отдаёт её -> активный Android подтягивает максимум за ~15 минут -> та же версия CELIKOM находит approved replacement без установки другой APK. Нельзя выдавать host-only tests за E2E на телефоне.
- Проверить временную зону и часы телефона: сохранённый snapshot считается пригодным до 7 дней, разовый запрос сгенерирован сервером.
- При миграции проверить новый `ApiContract.ORIGIN`, auth, TLS, БД и Android signing build inputs. Не переносить Hostinger SSH creds/API origins без проверки.
- Test.59 — текущая предыдущая тестовая версия для диагностики музыкальных сбоев; **Test.60 не вносит исправления в проблемные Pause/Seek RASKOL и «Дым»**, а только автоматический catalogue sync.
