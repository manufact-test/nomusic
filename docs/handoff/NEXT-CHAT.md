# CELIKOM — продолжение проекта в новом чате

## СРОЧНОЕ ОБНОВЛЕНИЕ: 9 октября 2026 — live audio 0.4.3

**Этот раздел новее состояния от 8 октября ниже; старое "следующее действие" и старое состояние Stage 5 далее считать исторической записью.**

- Первый пользовательский MP3 (подтверждены права использования) загружен через File Manager в `celikom/shared/staging`; Track ID `144530503`, длительность `180872` ms, размер ~4.35 MB. Серверный импорт в private MySQL/audio approved mapping **replacement ID 1** выполнен. `FEATURE_REPLACEMENTS=1`, `FEATURE_ANALYTICS=0`. Бета-код владелец получил непосредственно из приватного Hostinger env; его нет в чате/Git/логах.
- Прямой remote `audio.src` был заблокирован CSP `media-src` Яндекс Музыки (скрин DevTools владельца). `extension/src/player/replacement-player.ts` в **0.4.3** использует `MediaSource` + `blob:` + 512KiB signed HTTP Range chunks; не буферизует целиком файл в JS. GitHub extension build [37848261630](https://github.com/manufact-test/nomusic/actions/runs/37848261630) 67/67 tests pass; main CI [37848269651](https://github.com/manufact-test/nomusic/actions/runs/37848269651) success.
- Авторизованный live HTTPS resolve, signed-audio CORS/Range smoke checked via restricted GitHub Actions [37846857378](https://github.com/manufact-test/nomusic/actions/runs/37846857378); edge не передаёт `Accept-Ranges`, но отвечает `206` с точным `Content-Range` и `audio/mpeg`.
- Владелец сообщил, что **реальный MP3 с Hostinger заиграл** в 0.4.3 (не встроенный сигнал), и подтвердил **все шесть** функциональных тестов: пауза/воспроизведение, seek вперёд/назад, seek почти в конец, громкость/mute, следующий трек → оригинал, Return Original.
- **Сейчас**: выполнить углублённый live-stability gate по [CELIKOM-STAGE5-LIVE-AUDIO.md](../test-plans/CELIKOM-STAGE5-LIVE-AUDIO.md). Затем закончить repeat-deploy с сохранением audio/env, backup/restore и monitoring. Не считать Stage 5 закрытым и **не мержить PR #6** без оценки gate. Серверный deployed app release остаётся 0.4.0-e0461f56..., хотя клиентское расширение 0.4.3 — это нормально.
- Пользователь попросил объединять действия в удобные блоки, **не заставлять делать по одному микрошагу**, пока не возникнет непонятность. Никаких повторных проверок подключения/token или переустановок без необходимости. В Chrome при проблеме диагностика копируется из активной вкладки Яндекс Музыки, никогда не просить подписанные URL или реальный токен.

Состояние на 8 октября 2026, 21:26 Europe/Warsaw. Это передача выполнения, а не отдельная спецификация. Сверить последующие изменения ветки и deployment перед новыми операциями.

## Основные документы

- Мастер-ТЗ: `CELIKOM_Master_TZ_MVP_v1.4.docx`. Постоянный идентификатор основного файла: `libfile_957c4af62ffc8191ab6b9ef4f370365d`.
- Карта работ: `CELIKOM_Plan_Rabot_MVP_v1.5.docx`. Постоянный идентификатор: `libfile_2a8622d33d248191ba194b57e9c27567`.
- Предыдущие master v1.3 / plan v1.4 заменены новыми версиями этих же основных документов.
- Исполнение: [project-status.md](../project-status.md), [current-environment.md](../deployment/current-environment.md), [Hostinger runbook](../deployment/hostinger-private-test.md).

## Как работать с владельцем

Работать самостоятельно и принимать решения до реальной необходимости его помощи. Не повторять настройку уже работающих доступов. В Hostinger объяснять по одному простому действию и опираться на текущий экран. Пользователь предпочитает обычный чат; управление его локальным Chrome не настроено. Реальный Яндекс проверяет владелец, присылая результат и JSON. Код, сборки, CI и серверные операции выполняет агент.

## Код и ветки

- Репозиторий: https://github.com/manufact-test/nomusic . Сейчас public по решению владельца.
- Текущая ветка: `feature/api-range`; открытый PR: https://github.com/manufact-test/nomusic/pull/6 . Не считать его слитым. `main`/`develop` ещё не содержат всех Stage 4–5 изменений.
- PR #5 Stage 3 слит в develop: `b346ff2eee6486a48944cbf8eb35c2458c6108a7`.
- Сервер развёрнут из `e0461f56b77e6fea86493e25c39af4a8eddbabb6`. Последующие commits этой ветки обновляют документы; они не означают новый deployment.
- В предыдущем окружении shell git push не имел credentials; изменения публиковались через GitHub GitData create_tree → create_commit → update_ref с expected SHA. Локальные и удалённые commit metadata могут отличаться при одинаковом tree. Проверять remote head/tree; force push не нужен.
- Локальная копия в предыдущем чате: `/workspace/scratch/c1a57beacbb6/celikom`. Если отсутствует в новом чате, получить актуальный checkout именно `feature/api-range`; старый scratch не гарантируется.

## Что уже принято

| Этап | Подтверждённое состояние |
| --- | --- |
| 0–1 | PoC и production foundation закрыты 7 октября |
| 2 | Принят владельцем на 0.2.1; здоровые startup/bridge, Track ID и player events; PR #4 слит |
| 3 | Принят владельцем на 0.3.2; local replacement и manual bypass; PR #5 слит |
| 4 | 0.4.0 automated gate passed: реальный MySQL, exact-ID catalog, signed Range, native Chromium WAV decode/seek/play; PR #6 открыт |
| 5 | API/MySQL/HTTPS развёрнуты; живой MP3/WAV и оставшиеся operations checks ещё впереди |

Не превращать приёмку владельцем Stage 3 в утверждение независимого полного прогона. Старые `guard-lost:master-binding-changed` остаются наблюдениями без установленной причины; проверить в следующем живом тесте.

## Hostinger уже работает

- API origin: https://darkred-camel-588676.hostingersite.com . Health: `/api/v1/health`; config: `/api/v1/config`.
- Отдельный PHP/HTML сайт CELIKOM. Другие сайты аккаунта не менять.
- SSH ACTIVE: `92.113.19.189:65002`, user `u235811320`. Прямой SSH из прежней чат-среды возвращал `Network is unreachable`; GitHub Actions SSH работает.
- MySQL database/user: `u235811320_celikom`.
- Секреты Actions `HOSTINGER_SSH_KEY` и `HOSTINGER_DB_PASSWORD` уже добавлены владельцем. Не запрашивать заново и не пытаться читать их значения.
- Серверные `.env`, подпись, privacy key и beta-код приватны. Не выводить в публичные logs/artifacts или чат. Ключи созданы на сервере, не в Git.
- Приватная база приложения: `/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom`.
- Shared: `shared/env` 0600, `shared/audio` и `shared/staging` 0700, вне `public_html`. `current` — symlink на release.
- Активный release: `0.4.0-e0461f56b77e6fea86493e25c39af4a8eddbabb6`.
- CLI PHP проекта: `/opt/alt/php83/usr/bin/php` — 8.3.33. Default SSH PHP 8.2.33, использовать явный binary. HTTP PHP 8.3.33 выбран только в `.htaccess` CELIKOM.
- **FEATURE_REPLACEMENTS=0, FEATURE_ANALYTICS=0. Первый реальный файл не импортирован.**

Успешный deploy: https://github.com/manufact-test/nomusic/actions/runs/37824995803 . CI того же приложения: https://github.com/manufact-test/nomusic/actions/runs/37825005035 . Проверены реальные HTTP PDO/MySQL, миграция и no-op повтор, HTTPS health/config, Yandex CORS, unauthenticated resolve 401. Временный probe удалён. Host-side rollback проверен на изолированных filesystem/HTTP fixtures; deliberate live outage/rollback drill не проводился.

## Автоматизация

- `.github/workflows/hostinger-preflight.yml` — доступ/runtime checks.
- `.github/workflows/hostinger-deploy.yml` — CI, immutable package, SSH/SFTP deploy, migration, HTTPS checks.
- Запуск нового deploy: изменить `.github/deploy/hostinger-request.json` в `feature/api-range` или `develop`. После CI проверить actual deployment job/logs, а не только общий зелёный workflow.
- `.github/scripts/hostinger-deploy.sh` и `hostinger-activate.sh` привязаны к отдельному CELIKOM site, pin server key и проверяют package checksum. Существующий shared/env сохраняется.
- **Текущий workflow не импортирует песни, не переключает flags и не выдаёт владельцу beta-код.** Следующую необходимую операцию подготовить отдельным проверенным Actions шагом или приватной SSH-командой.
- Серверный ED25519 fingerprint: `SHA256:Uiu45j1QLdnNz8eIZCkle9WexPRz8hdUUr3LLGyNR5Y`. Клиентский fingerprint: `SHA256:Q6FyifXRq6garceQdIIjBmXhkk81Ic1p/x9JTSYHWUk`. Не путать. Pin был получен при первом соединении с hPanel-confirmed endpoint, это не отдельная out-of-band проверка.

## Немедленный следующий шаг

Последняя инструкция владельцу: открыть **Hostinger → Files → File Manager** и прислать экран. Продолжать отсюда.

1. Проверить доступ к приватному `celikom/shared/staging`, соседнему с `public_html`. Если File Manager заперт внутри web root, использовать SFTP с уже настроенным ключом; не класть аудио в публичный корень.
2. Получить проверенный владельцем MP3/WAV, точный Яндекс Track ID и измеренную длительность. Существующие JSON с ID — примеры прошлого теста, а не выбранный файл для импорта. Не угадывать соответствие песни/ID или длительность.
3. CLI import `current/bin/import-test-audio.php --file=ABS_PRIVATE_PATH --track-id=EXACT_ID --duration-ms=MEASURED_MS --confirm-reviewed` через PHP 8.3. MIME/size до 30 MiB/SHA dedup проверяет importer. Клиент допускает расхождение длительностей ±1500 ms. Автоматическая модерация и user upload UI отсутствуют.
4. После успешного import проверить approved exact mapping и файл; включить `FEATURE_REPLACEMENTS=1`. Analytics оставить 0. Доступ beta-code дать владельцу приватным способом, без логов/Git/чат-публикации всего env.
5. Установить 0.4.0 под наш API origin, обновить вкладку Яндекс, оставить testTrackId пустым, beta-код в developer details, Старт. Встроенный сигнал остаётся отдельным developer test; он не доказывает remote MP3.
6. Пройти живой checklist, записать обезличенный результат. Затем закончить repeat deploy/shared preservation, backup/restore и monitoring этапа 5; только после приёмки переходить к этапу 6.

## Сборка и живой gate

```bash
CELIKOM_API_BASE_URL=https://darkred-camel-588676.hostingersite.com npm run build:extension
node extension/scripts/validate-manifest.mjs
```

ZIP в `extension/dist/celikom-extension-0.4.0.zip`; распакованная сборка в `extension/dist/unpacked`. В прошлом чате ZIP уже собран под этот origin и передан владельцу. Обычный `npm run validate`/CI может пересобрать extension без origin; перед передачей проверить `api/config.json` и API host permission, затем при необходимости выполнить команду выше. Секреты в bundle не включаются.

Живой gate: mapped ID → реальный файл; unmapped → original; pause/resume/seek/volume/mute/rate; next/previous/SPA/reload; «Вернуть оригинал» держится до смены ID или явного Старт. Ошибка API, отсутствующий файл, autoplay rejection, истёкшая подпись → fail-open. Проверить реальный HTTPS Range и CSP страницы Яндекса, минимум 2–3 минуты стабильной подмены после seek. CI fixture не доказывает CSP/autoplay на Яндексе. Signed URL живёт 10 минут; истечение возвращает original, новую попытку инициирует Старт.

## Дальнейший scope

Минималистичный интерфейс: Старт, Стоп, Вернуть оригинал, Добавить трек; диагностика отдельно. Меню Подписка и друзья: оплата, promo/referral code, управление подпиской. Admin analytics: новые/активные/возвращающиеся, first paid/renewed/churn, full-price/discounted и источники скидок; финансовая истина из server billing ledger. Сейчас реализован только фундамент событий, аналитика выключена.

Порядок этапов 6–18 сохраняется: общая библиотека → uploads/dedup → moderation/admin → accounts/devices → trial/entitlement → billing → referrals/rewards → incidents → hardening → closed Alpha → Android PoC → Android Beta APK с сайта → final source/infrastructure privacy gate. Перед клиентским релизом public GitHub закрыть либо перенести в private Git с проверенным backup. Production provider пока не выбран, Hostinger — текущий тестовый старт. Android playback внутри стороннего native app и Apple app не являются готовыми функциями.
