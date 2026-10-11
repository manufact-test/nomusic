> **11.10.2026 — админка 0.4.23, клиент остаётся 0.4.22.**
> Владелец подтвердил исправление popup с другой активной вкладки и наличие нового раздела.
> По двум скриншотам три панели навигации объединены в одну, с переносом пунктов;
> у формы сбоя подпись над textarea, кнопка ниже, отступы и мобильные размеры исправлены.
> [CI/MySQL/Chromium PASS](https://github.com/manufact-test/nomusic/actions/runs/38150560659),
> [MariaDB PASS](https://github.com/manufact-test/nomusic/actions/runs/38150557360):
> nav по ролям/flags и реальные browser geometry на desktop/tablet/mobile.
> [Snapshot PASS](https://github.com/manufact-test/nomusic/actions/runs/38150557356): 36 SQL таблиц, 12 audio.
> [Deploy PASS, attempt 2](https://github.com/manufact-test/nomusic/actions/runs/38150746335/attempts/2),
> release `0.4.23-df8bd247b9ae0a6ff1ecc75f453403fa84be8529`.
> Первая попытка остановилась на SSH timeout до загрузки; повтор успешен.
> [Read-only audit PASS](https://github.com/manufact-test/nomusic/actions/runs/38151006311):
> опубликованные unified nav и incident form проверены, digest данных/наград не изменился.
> Миграций и клиентских изменений нет; новые ZIP/Reload расширения не нужны.
> Для UI приёмки только обновить админку. Объявлять live сбой ради теста не требуется:
> это общий запрет подмены с сохранением времени доступа, start/resolve уже проверены на fixtures.
> Реальная оплата отсутствует; 11/12 и коммерческая часть 13 остаются частичными, PR #6 OPEN/unmerged.
> [Передача контекста](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/ADMIN-UI-2026-10-11.md).
> Эта запись имеет приоритет над историческим состоянием ниже.

> **11.10.2026 — 0.4.22: два исправления и независимая часть этапа 13.**
> Сервер `0.4.22-edf72f42112ac3b113942fe542710082d528243e` развёрнут: [Deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/38148930467).
> [CI/MySQL/Chromium PASS](https://github.com/manufact-test/nomusic/actions/runs/38148775909),
> [MariaDB PASS](https://github.com/manufact-test/nomusic/actions/runs/38148772120),
> [Snapshot PASS](https://github.com/manufact-test/nomusic/actions/runs/38148667363),
> [изолированный restore PASS](https://github.com/manufact-test/nomusic/actions/runs/38148772114).
> Popup работает с фактической вкладкой Яндекс Музыки, даже при другой активной вкладке/окне.
> Временные сбои bridge/worker/сети/плеера: fail-open и восстановление без повторного Start;
> ручные Original/Stop/logout сохраняются. Причина исходного зависания Яндекса не установлена.
> Owner-only «Сбои интеграции»: start/resolve, CSRF, точная UTC компенсация trial/paid fixtures,
> union пересечений, частичные сроки, повторные/параллельные resolve без второго начисления.
> Миграция 014 добавляет три таблицы; старые trial/grants и аккаунты не сбрасываются.
> Реальной платёжки/checkout/webhook/recurring pause-resume нет; этапы 11/12 остаются частичными.
> Этап 13: независимая реализация готова, ручная приёмка владельца и коммерческие зависимости открыты.
> Один полный клиент CELIKOM-0.4.22-full.zip: 2437844 bytes, SHA256 `df4deacdfb4bb97107b1dca3c0aeb6ce9e63a8f5c8dcb0d1b143577bec616eb8`.
> Финальный клиент: 164/164 теста и [CI/MySQL/Chromium PASS](https://github.com/manufact-test/nomusic/actions/runs/38149236196).
> [Read-only audit нового release PASS](https://github.com/manufact-test/nomusic/actions/runs/38149306572):
> migration 014, owner view и пустое состояние incidents; digest аккаунтов/сроков/наград/каталога не изменился.
> Биллинг и paid referrals выключены; реальный инцидент не объявлялся. Пакет ожидает одну ручную приёмку владельца.
> PR #6 OPEN/unmerged, Issue #7 OPEN, прежняя 0.4.21 принята. Сохранять рабочую резервную 0.4.4.
> [Поведение и единая проверка](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/test-plans/CELIKOM-STAGE13-INCIDENTS.md).
> Эта запись имеет приоритет над историческими checkpoint ниже; не повторять принятую QA этапов 10/12.

> **11.10.2026 — пакет автоматических наград принят; UI доработки 0.4.19 готовы.**
> Владелец подтвердил две последовательные загрузки, появление версий в админке,
> группировку аккаунтов, автоматические проценты и перенос остатка; выставил
> собственные параметры бонусов. Пакет начисления/переноса закрыт по его подтверждению.
> Единственный оставшийся дефект админки — возврат к началу страницы при раскрытии —
> исправлен на сервере: native details, ленивый GET истории внутри карточки,
> сворачивание и повторное раскрытие без перехода; страницы песен также внутри.
> Backend release `0.4.18-6b04b9fce864c9201a03938583a29f1f1d1d4ea3`.
> [Deploy 38140319635 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38140319635),
> [MariaDB 38140209094 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38140209094),
> [snapshot 38140209143 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38140209143),
> [read-only audit 38140725866 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38140725866).
> Реальные reward_policy/ledger/allocations, accounts/sessions/trials/catalog/media сохранены.
> В админке разрешён только точный CSP hash скрипта; внешние fetch и произвольный
> inline script не разрешены. Четыре регрессионных сценария раскрытия/закрытия/
> позднего ответа/ошибки сессии и пагинации проходят. По 25 аккаунтов и песен.
> Chrome 0.4.19: «Старт» без локальной сессии немедленно возвращает требование входа
> до определения трека, trial activation и сетевого запроса. Блок аккаунта раскрывается,
> выделяется красный реальный border и заголовок, появляется понятная ошибка.
> Задержанный первоначальный status не удаляет подсказку; успешный вход снимает её.
> Account preview возвращает только boolean наличия сессии, не токены и не разрешение доступа.
> Toolbar C: серый при отсутствии подмены, зелёный только по здоровому heartbeat
> REPLACEMENT_ACTIVE из собственного Yandex content script после проверки доступа.
> Stop/logout/navigation/tab close/lost heartbeat возвращают серый; несколько вкладок
> учитываются вместе. Повторные heartbeat не перерисовывают иконку. Новых permissions нет.
> [CI 38140988356 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38140988356):
> 154 теста расширения, 17 прототипа, 4 disclosure сценария, PHP/MySQL и native Chromium.
> Backend повторно не разворачивается ради двух клиентских правок; полный клиент
> содержит все функции и прежний Hostinger API, оба MV3 worlds и VERSION 0.4.19.
> `CELIKOM-0.4.19-full.zip`, 2435343 bytes, SHA256
> `159c65fd971216b7ba313f009cd1ca97d040cf0b947f0d7c1417da8fcdb80807`.
> В текущей установке заменить файлы, Reload, обновить Яндекс. Аккаунт не сбрасывать.
> Следующая осмысленная ручная проверка: красный блок аккаунта при Start без входа
> и зелёная/серая иконка при фактической подмене/остановке; прежние загрузки и бонусы
> не просить перепроверять отдельно. Мелкие текстовые или серверные правки не выдавать
> отдельным установочным пакетом. Не повторять проверку второго реального компьютера.
> Весь этап 12 / Issue #13 OPEN: реальные платежи, применение скидки при оплате,
> qualification приглашений остаются отложенными до выбора провайдера.
> Этап 10 закрыт, PR #6 OPEN/unmerged, Issue #7 OPEN. Trial 3 дня без reset.
> Рабочую резервную 0.4.4 не удалять; Track 144530503/Replacement #1 и приватный MP3
> сохранять. Другие версии оставлять в фактических состояниях модерации владельца.
> Миграции 011–013 неизменяемы, новые изменения schema отсутствуют.

> **11.10.2026 — 0.4.18: три завершающие правки автоматических наград.**
> [Read-only audit 38138665844 — PASS, attempt 2](https://github.com/manufact-test/nomusic/actions/runs/38138665844):
> на точном release проверены свёрнутые аккаунты и история выбранного автора;
> digest users/sessions/trials/catalog/reward_policy/ledger/allocations не изменился.
> Первая попытка завершилась SSH connection timeout до запуска серверного скрипта;
> повтор успешен. Оплата и qualification приглашений по-прежнему отложены.
> Рабочий release `0.4.18-25e4982804b2235fd724ddc939d31d0dc8ccab8c`.
> [Deploy 38138462425 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38138462425):
> MariaDB schema без новых миграций, повторный migrate, HTTPS/CORS/401;
> существующие owner credentials и feature flags сохранены без ротации.
> [Изолированное восстановление 38138665846 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38138665846):
> SQL и приватные файлы восстановлены отдельно от действующего сайта.
> Владелец подтвердил автоматическое начисление процентов и перенос остатка
> на следующий месяц. Повторное одобрение бонусов не требуется.
> Исправлены обновление версии песни сразу после входа и последовательные
> загрузки разных песен: старая форма/MP3/идентификатор запроса сбрасываются
> при смене трека. Один клик открывает новую песню даже до очередного polling.
> Песня дополнительно сверяется после сетевой проверки; файл не отправляется
> к изменившемуся Track ID. Поздний ответ старой сессии не затирает статус входа.
> Начисления в админке сгруппированы по аккаунтам: число учтённых песен,
> сумма бонусов, раскрытие только выбранного аккаунта. Новейший вклад поднимает
> аккаунт вверх; внутри песни идут от новых к старым. По 25 аккаунтов и песен
> на странице, без загрузки всей многотысячной истории.
> [CI 38138380531 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38138380531):
> 147 тестов расширения, 17 прототипа, PHP/MySQL и native Chromium audio.
> [MariaDB 38138378392 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38138378392):
> группировка, порядок, 27 песен одного аккаунта и 27 аккаунтов, исторические бонусы.
> Первоначальный старый тест ожидал песню в свёрнутом списке: обновлён на
> раскрытие аккаунта, экранирование и роли продолжают проверяться.
> [Резервная копия до rollout 38138288953 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38138288953).
> Полный `CELIKOM-0.4.18-full.zip`, 2427258 bytes, SHA256
> `0a1bc00d2ce33b465122e7c487b2bac15f53dd39e4e3f3ea274e59780c73fdc3`.
> Обновлять текущую установку; аккаунт, пробный период и бонусы не сбрасывать.
> Короткая ручная проверка остаточных правок: войти при открытой Яндекс Музыке,
> отправить две разные новые версии подряд, раскрыть аккаунт в начислениях.
> Механика начислений/переноса принята; эти три исправления ожидают проверки владельца.
> Этап 12 / Issue #13 в целом остаётся OPEN: реальная оплата и квалификация
> приглашений отложены. Этап 10 закрыт; PR #6 OPEN/unmerged, Issue #7 OPEN.
> Рабочую резервную 0.4.4 не удалять, Track 144530503/Replacement #1 не менять;
> остальные песни сохраняют фактическую модерацию владельца. Миграции 011–013 не менять.

> **11.10.2026 — 0.4.17 развёрнута: автоматические бонусы и перенос процентов.**
> Рабочий release `0.4.17-4f926ea740d30dcf04703bf178e272e6922c516e`.
> [Deploy 38135908903 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38135908903).
> На Hostinger подтверждена MariaDB. Первый rollout остановился до переключения:
> синтаксис MySQL DROP CHECK не подошёл MariaDB, миграция 013 не применилась.
> Read-only диагностика подтвердила marker/column/table=0. Только после этого
> ещё не применённая миграция 013 исправлена на выбор DROP CONSTRAINT для MariaDB.
> Миграции 011/012 не изменялись. После успешного rollout 013 также неизменяема.
> [MariaDB 38135645996 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38135645996):
> 7 automatic/carry сценариев и исторические policy/grant тесты.
> [CI финального клиента 38136181230 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38136181230):
> 144 теста расширения, 17 прототипа, PHP/MySQL регресс и native Chromium.
> [Live user audit 38136070622 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38136070622):
> обычная сессия пользователя, полный MP3 девятью диапазонами, пробный доступ
> 3 дня, независимые устройства/refresh/logout, HTTPS upload и отдельное предложение,
> pending denied playback, GET rewards только собственного аккаунта, client grant 405.
> Fixtures удалены, реальные accounts/trials/catalog/private audio сохранены.
> [Reward integrity 38136178446 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38136178446):
> read-only audit точного release, policy/ledger/allocations/credentials сохранены.
> [Snapshot 38136178450 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38136178450):
> все 33 SQL таблицы, env и 8 audio.
> [Restore 38136300387 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38136300387):
> изолированно восстановлены файлы и полный SQL нового schema, live DB не заменялась.
> Pre-retry [restore 38135778796 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38135778796).
> Дополнительный диагностический stdout сначала мешал SQL export при restore-drill;
> диагностика исключена для restore-export, повтор успешно проверил чистый SQL поток.
> Live DB при восстановлении не заменялась.
> Полный ZIP `CELIKOM-0.4.17-full.zip`, SHA256
> `7767edcfa0c1c937e92d44e473b9e2fcb6ae5d2eb5ae2670d5fa769eec637e2c`,
> 2427015 bytes. Прежний Hostinger, оба MV3 worlds; аккаунт/сессии/пробный срок
> не сбрасывались. Пустой раздел бонусов скрыт до настройки правил или начислений.
> Ручная проверка: обновить текущую установку и админку, сохранить три настройки,
> загрузить из пользовательского аккаунта новую уникальную версию и одобрить её.
> Бонус должен появиться сразу без второй проверки. Для компактной проверки переноса
> временно 3%/предел 5%/30 дней: две разные новые версии дают 5% сейчас + 1% далее.
> После проверки сохранить коммерческий месячный предел, например 20%.
> Начисленные проценты/сроки/очередь прежних бонусов не переписываются при настройке.
> Применение к платежу, расходование/идемпотентность, повторные оплаты в месяце,
> возвраты и финансовое сочетание с referral/promo остаются в #12 до платежей.
> Stage12 открыт до оставшихся функций и owner acceptance; PR6 OPEN/unmerged,
> Issue7 OPEN. Яндекс startup ошибку не расследуем по решению владельца.

> [Snapshot нового live schema 38129853027 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129853027):
> 8 audio объектов, все 32 SQL таблицы (включая reward_ledger/reward_policy) и env.
> [Restore нового schema 38129932202 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129932202):
> закрытые файлы и SQL восстановлены изолированно, live данные не заменялись.
> ZIP 0.4.16 готов к одной содержательной owner-проверке; результаты ещё не получены.

> [Live unified audit 38129760860 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129760860):
> обычный user bearer, трёхдневный trial, независимые устройства, refresh/logout
> только одного устройства, signed HEAD/206 и полный MP3 девятью диапазонами,
> загрузка MP3 и отдельное предложение без файла, dedupe, pending denied playback.
> Проверка выполнена на новом live release, без отдельного API_TEST_TOKEN для клиента.
> Сохранность прежних catalog/media/accounts/trials/sessions подтверждена после
> удаления только временных QA-записей. Старый audit сначала отказал новой версии
> по allowlist до каких-либо записей; разрешён только audit точного release SHA,
> старые reset-trials/enable операции для этого release не разрешены.
> [Stage12 audit 38129629193 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129629193).
> Ручная проверка новых наград ещё ожидается; рабочий playback не считается
> повторно принятым владельцем лишь по автоматическому HTTP smoke.

> **11.10.2026 — Stage12 развёрнут, подготовка ручной проверки 0.4.16.**
> Hostinger release `0.4.16-dd54afb774baefc90c2c059a6231c85a0442b9b6`,
> [deploy 38129391202 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129391202).
> Миграции 009–012 additive; старые owner credentials и flags сохранены, не ротированы.
> [Enable 38129558574 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129558574):
> изменён только FEATURE_REWARD_ELIGIBILITY=1, digest аккаунтов/устройств/сессий/
> trials/catalog/media/policy сохранён, HTTPS rewards без bearer = 401.
> Owner-раздел «Награды за вклад» включён; правила остаются выключенными/нулевыми.
> FEATURE_BILLING_VIEWS=0, FEATURE_REFERRAL_ATTRIBUTION=0, реальные платежи/применение
> скидки/списание бонуса/paid entitlement не включены. Исторические авторы не backfill.
> Полный Chrome ZIP 0.4.16 SHA256 `5a89f46b17163d09479f561473a6a683d5f49d4d019bddbb52d64f3496e916eb`;
> включает правку отступа без трека, pin на прежний Hostinger API, оба MV3 worlds.
> Это одно расширение, установленную резервную 0.4.4 не удалять. Ручная проверка:
> новая загрузка → approve версии → pending-вклад → grant/revoke/журнал в админке,
> затем обычный playback/оригинал и отсутствие отступа. Не давать отдельный текст на QA.
> Старые документы ниже — история, не актуальное «сервер 0.4.11 не обновлялся».
> Этап 12 частичный; не закрывать до qualification/реальных скидок и owner acceptance.

# CELIKOM — current private-test environment

Recorded: 2026-10-09. Source of truth for requirements remains CELIKOM Master TZ MVP v1.4 and Work Plan MVP v1.5. This file captures measured deployment facts, not a production-security approval.

## Hostinger / API

- Dedicated Hostinger PHP website: https://darkred-camel-588676.hostingersite.com (temporary test hostname).
- Hostinger hPanel: https://hpanel.hostinger.com/websites/darkred-camel-588676.hostingersite.com
- Private application: /home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom
- Public site document root: sibling public_html; release package, SQL migrations, credentials and user audio live outside web root.
- SSH: 92.113.19.189:65002, account u235811320. GitHub Actions SSH key and DB password are already configured as secrets; do not ask user to reveal or rotate them.
- Application CLI/runtime: PHP 8.3.33 with pdo_mysql and fileinfo. MySQL user/database: u235811320_celikom.
- Active immutable server release: **0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d**. The server API reports version **0.4.0** by design; Chrome extension version is **0.4.4**. Deployment workflow was fixed to independently validate the API package version.
- Feature flags: FEATURE_REPLACEMENTS=1, FEATURE_ANALYTICS=0. Signed audio and owner-only temporary API token stored privately; no secrets are in Git or artifacts.

## Real audio and playback

- Reviewed private MP3 is stored under shared/audio and associated with exact Yandex Track ID 144530503 via approved MySQL replacement ID 1; measured duration 180872 ms; audio length 4345176 bytes.
- Browser owner acceptance: 6 of 6 functional and 6 of 6 stability scenarios on 0.4.4. CSP-compatible MediaSource blob backed by 512 KiB HTTP Range streaming.
- Re-enabling a disabled Chrome extension on an already-open Yandex Music tab can require refreshing that page once; accepted for current MVP. Does not block playback or safety.

## Verified Hostinger operations on 2026-10-09

- Read-only production integrity (private env, approved DB mapping, on-disk SHA-256, public health/config): https://github.com/manufact-test/nomusic/actions/runs/37903708919
- On-host private recovery snapshot (private config + audio + SQL for six database tables): https://github.com/manufact-test/nomusic/actions/runs/37903842547
- Isolated config/audio restoration and recovery of the same SQL schema/records into a disposable runner MySQL instance: https://github.com/manufact-test/nomusic/actions/runs/37903962631
- Repeated immutable production-server deployment with migration idempotence, PHP/MySQL runtime and HTTPS checks: https://github.com/manufact-test/nomusic/actions/runs/37904158336
- Post-deployment SHA-256 equality for original private env/audio and six MySQL row counts against the pre-deploy snapshot: https://github.com/manufact-test/nomusic/actions/runs/37904416817
- Internal authorized resolve + public HTTPS signed-audio HEAD/Range/CORS/206: https://github.com/manufact-test/nomusic/actions/runs/37904551511
- External public endpoint monitoring configured at a six-hour interval. Alert only on confirmed health/config/authorization failure; no tokens are needed.
- New operations runbook: [Hostinger Stage 5 operations](hostinger-stage5-operations.md).

## Limits and release safety

- The snapshot is **on the same Hostinger account**, not an offsite disaster-recovery backup. Secure independent backup/rotation is future production hardening.
- Restore was exercised for files in isolated storage and SQL on disposable MySQL; the live site's database was not overwritten. No intentional live outage/rollback drill was run; the activation rollback was previously validated on isolated fixtures.
- Public client release is **not authorized**: accounts, billing, end-user upload/moderation, permissions hardening and repository privacy remain later stages.
- PR #6 remains **open and unmerged**; project source work remains on feature/api-range. Separate future enhancement: auto reconnect after Chrome disable/re-enable.

Never print, commit or attach private keys, database credentials, API bearer tokens, private backup contents or signed audio URLs.
