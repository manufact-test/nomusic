> **12.10.2026 МСК — поддержка 0.4.30 развёрнута.** Форма CELIKOM → обращения в админке → ответ в приложении и через существующий SMTP регистрации; копии новых обращений на CELIKOM_MAIL_FROM. Backend release 0.4.30-c9b857776fed0fe80725c64d2091971de9c3583f; миграция016, snapshot/data audit/isolated restore PASS (38183803526). CI38183645111 и38183806786 PASS; configured extension38183641658 PASS. Android0.3.1 — read-only диагностика, Honor50 exact ID/native replacement/crash/physical routes ещё НЕ приняты. Owner пока установил0.4.28;0.4.30 требует только проверки нового обращения/ответа/email. PR6 OPEN/unmerged;15 исключён,16 частичный,17 не начат. [Приоритетная контрольная точка](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/CHECKPOINT-2026-10-12.md).

> **12.10.2026 МСК — native diagnostic0.3.0-probe подготовлен для Honor50 по согласованию владельца.** Нет WebView/login/подмены звука; read-only MediaSession + AudioEffect events, ручной отчёт, no INTERNET/microphone. Код9d50315, native CI38179310074 PASS (lint/build/2 API35 tests/font1.3), общий CI38179314385 PASS. Реальный Яндекс ещё НЕ проверен. [Шаги и границы](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/ANDROID-NATIVE-PROBE-OWNER-2026-10-12.md). Stage16partial/17notstarted/15excluded; PR6OPEN/unmerged, backend/extension/live data сохранены. Этот блок приоритетнее старой WebView-передачи.

> Native research: owned cross-app attenuation, independent alternate playback and explicit-release restoration confirmed on API29/35, run38177741159. Real Yandex session/Track ID, crash restore and physical routes remain unproven; see docs/spikes/ANDROID-NATIVE-COMPANION-2026-10-12.md.

> **12.10.2026 МСК — владелец отклонил Android WebView; нужен companion установленной Яндекс Музыки.**
> Android0.2.0 не решает требуемый сценарий и не принят. Владелец не продолжает проверку встроенного сайта. Требование: Яндекс Музыка остаётся своим приложением/master-плеером; CELIKOM работает рядом, включая screen-off/фон/наушники/автомобиль. Иконка, обрезание текста, ложные статусы и простой канал техподдержки зафиксированы.
> Проверяется конкретный кандидат: штатное подключение стороннего обработчика аудиосессии (как эквалайзера) + MediaSession. Нет доказательства native Yandex Track ID/mute/sync/physical routes; два owned research APK не являются продуктовой поставкой или service PASS. [Исследование и актуальные границы](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/ANDROID-NATIVE-COMPANION-2026-10-12.md).
> Stage16 частичный,17 не начат,15 исключён; никаких новых Alpha gates. Backend/extension0.4.28/live данные сохранены, PR6 OPEN/unmerged. Этот блок отменяет прежнее указание продолжать owner WebView playback check и имеет приоритет над историей ниже.

> **11.10.2026 23:56 МСК — Android0.2.0: готов к личной проверке реальной подмены.**
> Владелец23:25МСК разрешил реализацию при региональном блокере CI и проверку на своём телефоне. Приложение открывает Яндекс в WebView, использует общие core/adapter/OriginalAudioGuard и native MediaPlayer для альтернативы из существующего API. Добавлены native login/register/email verification/reset/Keystore session+refresh, promo/entitlement, public incident UI и Moscow dates. Это содержательный PoC, а не прежние fixture controls.
> Android код e65de5a0d28be59b6fd76c546c269dfddcbcfab0; Android38173802054 PASS (JS3/unit7/lint/build/native6), общий CI38173806601 PASS. APK CELIKOM-Android-0.2.0.apk:10968664B, SHA256 4aa2e6510d3935f2ac1994d47a8bd5f4b8d098e3d5435c36dc2edd2c0b209585, закрытая передача владельцу. Реальный сервис на CI снова показал региональный gate: playback НЕ подтверждён. Native/controller/crypto/UI tests не являются service proof.
> Для проверки держать приложение открытым: foreground-only PoC останавливает подмену при background/screen off; production signing/фоновый playback и остальные Android экраны относятся к17. Этап16 частичный до owner service proof;17 не начат;15 исключён, Alpha gate не нужен. [Шаги владельца](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/ANDROID-OWNER-CHECK-2026-10-11.md), [полные границы/доказательства](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/android-playback.md).
> Extension0.4.28 и backend0.4.28-29802edf4a4c071662639a2eb475915b9bf17bb8 сохранены. Нет live deployment/migrations/grants/incidents/reset; account/session/trial/entitlement/catalog/reward данные не менялись тестами. Платёжные11/12/коммерческие13 частичные; операционные14/приватизация18 и Issues7/10/11/12/13 сохраняются; PR6 OPEN/unmerged. Этот блок приоритетнее истории ниже.

> **11.10.2026 23:05 МСК — реальный Android surface probe.**
> CI 38170400164 PASS (build/unit/lint/native harness), общий CI 38170404247 PASS; код 8bab30bbb6537880541cbdf3d0cff51208bab53d. Яндекс на CI runner показал недоступность в регионе: media/Track ID отсутствуют, service playback НЕ подтверждён. Нужна проверка при легитимном доступе из поддерживаемого региона; ограничения не обходились. 16 частичный, 17 не начат, 15 исключён. Владелец ждёт содержательную готовую версию с реальной подменой: новые промежуточные APK не доставлять. Backend/extension/live данные сохранены, PR #6 OPEN/unmerged. Подробности: [Android PoC](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/android-playback.md). Этот блок имеет приоритет над историей ниже.

> **11.10.2026 — этап 16 начат, Android diagnostic 0.1.0-spike.**
> Владелец сообщил, что расширение/промокоды работают и разрешил следующий этап. Проверка кода наград подтверждает независимость бессрочного promo entitlement от процентной policy/переноса месяца; реальные данные не изменялись.
> Kotlin/Compose spike: собственные native audio fixtures, exact fixture state, play/pause/seek/next/previous/Original/fail-open, lifecycle/focus suspend; optional общий login/entitlement API. Это не доказательство подмены Яндекс.Музыки. Backend headers platform/version пока не сохраняются; мобильный dev registration и service playback flag не включены.
> Android unit/lint/debug build и API35 native emulator 38168453192 PASS; общий CI 38168457150 PASS. Диагностический APK доставляется закрыто, публичный artifact содержит только CMS AES-256-GCM envelope. APK SHA256 `dc54faa3427d6bf5fbc17d9638116f5ffe07bfd28ace1083de4abdfe3405ba52`.
> Этап 16 ЧАСТИЧНЫЙ: physical device, реальный login/network/focus/process death и конкретный допустимый Yandex surface не проверены. NO-GO включению Яндекс playback в Beta до доказательства surface; companion-only scope не принят автоматически. 17 не начат; 15 исключён. Платежные зависимости, операционные обязательства 14, приватизация 18 и Issues #7/#10/#11/#12/#13 сохраняются. PR #6 OPEN/unmerged.
> Extension 0.4.28/backend `0.4.28-29802edf4a4c071662639a2eb475915b9bf17bb8` сохраняются, нет новой live deployment/migrations/grants/incidents/reset. Подробности: [Android PoC](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/spikes/android-playback.md). Этот блок имеет приоритет над историей ниже.

> **11.10.2026 — оформление промокодов и прокрутки: CELIKOM 0.4.28 (актуальная передача).**
> Владелец подтвердил установленную 0.4.27, реальное создание промокода и одну активацию; механизм работает. Значения реального кода/аккаунта не публикуются. Ручная приёмка нового оформления 0.4.28 ещё не выполнена.
> Поля формы выровнены без растягивания при раскрытии даты/«Навсегда». «Название» и «Промокод» — отдельные колонки, кнопки по центру строки, повтор «Навсегда» убран. Единый клиент 0.4.28 добавляет отступ возле фактической прокрутки во всех экранах аккаунта; без прокрутки дополнительного отступа нет.
> CI/MySQL/native Chromium 38166683446 и 38166735759 PASS; 177 клиентских тестов, проверки формы/таблиц desktop+narrow, прокрутки login/register/verify/recovery/account и раскрытия/закрытия промокода. Configured ZIP 38166732141 PASS; полный архив SHA256 `62ec04dfb9726540709f4d627a6fa114d3598784bc2d08dd57f4e2b568669a1c`. Snapshot 38166732105 PASS: 12 audio / 39 SQL tables. Deploy 38167055702: PASS; backend `0.4.28-29802edf4a4c071662639a2eb475915b9bf17bb8` развёрнут, HTTPS health/config/CORS/unauthorized checks PASS.
> Нет новых миграций/reset/backfill, real grants/payments/incidents; данные и policy/ledger/allocations сохранены. PR #6 OPEN/unmerged. Этап 15 исключён; платежные зависимости и незакрытые 14/16/17/18 сохраняются. Следующая независимая работа — Android PoC 16 с доказательством разрешённого playback surface, без Alpha gate.
> Подробности: [Promo design and scroll spacing](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/PROMO-DESIGN-SCROLL-2026-10-11.md). Этот блок имеет приоритет над историческими статусами ниже.

> **11.10.2026 — московское время и исправление формы промокода (последнее уточнение владельца).**
> «Навсегда» сгруппировано со сроком доступа; поясняющий абзац удалён. Дата активации скрыта до выбора «До указанной даты» и появляется под этим выбором. Сам переключатель периода оставлен как принят владельцем, без нового значения по умолчанию.
> Ввод/отображение дат и пользовательские календарные периоды — `Europe/Moscow`. Время компьютера не влияет на срок, показанный расширением. UTC остаётся только внутренним форматом абсолютных временных меток и расчёта длительности/incident compensation; сохранённые сроки, policy, ledger и allocations не переписаны. Новые календарные месяцы наград — по Москве. Старые UTC analytics aggregates сохранены, текущий обзор использует московские границы на сохранённых raw events (с их сроком хранения).
> Клиент `0.4.27` — полный единый configured ZIP; установка этой версии владельцем и ручное создание/активация промокодов ещё не подтверждены. Ранее установленная `0.4.26` работает по сообщению владельца.
> CI/MySQL/native Chromium `38164907938` и MariaDB `38164904828` PASS; 177 клиентских тестов, форма desktop/mobile, точный deadline по Москве, границы месяца и сохранение прежних начислений. Snapshot `38164945424`: 12 audio / 39 SQL tables PASS. Выкладка `38165076903` PASS; backend `0.4.27-4488693f440c50c15a4ce401aa0000ff1c0f3f8f` развёрнут.
> Подробности: [MOSCOW-TIME-PROMO-FORM-2026-10-11.md](docs/decisions/MOSCOW-TIME-PROMO-FORM-2026-10-11.md). Нет новых миграций, real grants/payments/incidents. PR #6 не слит; этап 15 исключён; незакрытые 14/16/17/18 и платёжные зависимости сохраняются. Этот блок имеет приоритет над историческими статусами ниже.

> **Проверка после выкладки 38163057100 PASS:** все шесть старых/новых адресов с авторизацией вернули HTTP 200 за 0.011–0.019 с; snapshot 12 audio / 39 SQL tables PASS.

> **11.10.2026 — исправление админки промокодов после сообщения владельца о 504.**
> Backend `0.4.26-03938e9abf0db8d641abad42b0f07271d3b18c23` развёрнут. Создание — отдельная страница; «Промокоды / Активации» — компактное меню с текущим разделом, без дублирующих действий.
> Прямые пути: `/admin/promos`, `/admin/promos/new`, `/admin/promos/activations`; старые query-переходы совместимы. Форма создания больше не запрашивает и не показывает список.
> CI/MySQL/Chromium 38162865797, MariaDB 38162862533 и deploy 38162862461 PASS; в изолированных fixtures проверены новые страницы и POST создания конечного/бессрочного кода.
> Причина исходного 504 не доказана: текущий серверный рендер <0.001s; прежние авторизованные HTTPS страницы дали 200 за 13–21ms. Подробно: [Promo admin hotfix](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/PROMO-ADMIN-HOTFIX-2026-10-11.md).
> Расширение 0.4.26 менять не нужно. Владелец сообщил, что расширение работает; проверку исправленной админки за него не отмечать. Новых миграций, real codes/grants, payment или incident нет. Все прежние ограничения этапов 11–18 сохраняются.
> Эта запись имеет приоритет над историческими статусами ниже.

> **11.10.2026 — owner-промокоды реализованы: единый CELIKOM 0.4.26.**
> Backend `0.4.26-d04bb69dc3fc1f149c5203db522978f00c8a7cb7` развёрнут. Клиент 0.4.26 подготовлен; последняя подтверждённая установка владельца — 0.4.25.
> 100%: бесплатный доступ, добавление дней к остатку (7 + 30 = 37) или «Навсегда» с отдельным подтверждением создания.
> «Промокоды» / «Активации»: аккаунт, код, срок, индивидуальный отзыв, история и аудит. Один аккаунт / один код / одна активация; общий лимит по умолчанию 1, настраивается владельцем, конкурентные запросы атомарны.
> Активация в аккаунте клиента; общий EntitlementService и incident freeze. Промокод не payment / paid referral / reward. Первый «Старт» сохраняет принятое поведение trial.
> 176 тестов клиента PASS; CI/MySQL/native Chromium 38159681816, MariaDB 38159678661, configured ZIP 38159457448, snapshot 38159457466, isolated restore 38159538579, deploy 38159678651, post-deploy integrity 38161546039 — PASS.
> Миграция 015 только добавляет таблицы. Применённые миграции, credentials, flags, accounts/sessions/trials/entitlements/audio/catalog/moderation/reward policy/ledger/allocations не сбрасывались. Реальные коды/grants не выдавались, real incident не запускался.
> Скидки ниже 100% сохранены как настройки, активация отложена до оплаты; monthly/short-window правила и финансовые зависимости 11–13 остаются частичными.
> Далее Android PoC 16 без Alpha и ожидания провайдера: требуется доказательство конкретного разрешённого playback surface. 15 исключён; Beta 17 и приватизация 18 сохраняются. Операционные обязательства 14 и Issues #7/#10 не закрыты; PR #6 OPEN/unmerged.
> Подробно: [Промокоды](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/PROMOS-2026-10-11.md). Эта запись имеет приоритет над историческими статусами ниже.

> **11.10.2026 — независимый security-пакет этапа 14: CELIKOM 0.4.25.**
> Backend `0.4.25-35428e3854769bf4e63c5c6f980fc5756a5581a8` развёрнут; полный единый клиент 0.4.25 подготовлен.
> Владелец подтвердил установку 0.4.25 и работу: «Да, всё хорошо, установил, распаковал, всё работает, можно идти дальше».
> Закрыты найденные пробелы worker sender/intent, bounded auth JSON, write quotas account/device/IP и build secret/dependency gate.
> CI/MySQL/native Chromium 38156426516 PASS; MariaDB 38156423107 PASS, включая четыре quota workers / 32 attempts; configured ZIP 38155884847 PASS.
> Snapshot 38155683083, isolated restore 38155787902, deploy 38155884937, read-only integrity 38156091112 — PASS.
> Новых миграций/reset/backfill/live incident нет; private env, аудио и исторические row counts сохранены.
> Полное закрытие 14 не заявлено: offsite backup, provider-log redaction/rotation и capacity monitoring требуют операционной проверки.
> Далее разрешён Android PoC 16 без Alpha/провайдера; 15 исключён, Beta 17 и приватизация 18 сохраняются.
> Owner-промокоды 12 остаются отдельной обязательной задачей: код/grants этим пакетом не созданы. Billing 11–13 частичные.
> PR #6 OPEN/unmerged, Issue #7/#10/#11/#12/#13 OPEN. Подробно: [Stage14](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/STAGE14-2026-10-11.md).
> Эта запись имеет приоритет над историческими статусами ниже.

> **11.10.2026 — текущая передача: клиент 0.4.24 установлен; далее этап 14.**
> Независимая часть 13 реализована; real billing/checkout/recurring и платёжные части 11–13 не подключены.
> Владелец исключил отдельную Alpha 15: текущее использование втроём, без новой кампании и gate.
> Нумерация сохранена: после 14 Android PoC 16, Beta 17; приватизация 18 до выпуска клиентам.
> Owner-промокоды бесплатного доступа — обязательная независимая задача 12, пока не реализована; провайдер не нужен.
> Полная актуальная запись: [CHECKPOINT-2026-10-11.md](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/CHECKPOINT-2026-10-11.md).
> Решение владельца: [ROADMAP-NO-ALPHA-2026-10-11.md](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/ROADMAP-NO-ALPHA-2026-10-11.md).
> Эта запись имеет приоритет над историческими статусами ниже. PR #6 OPEN/unmerged, Issue #7 OPEN.

> **11.10.2026 — клиент 0.4.24: красный экран объявленного сбоя.**
> Вместо всех музыкальных кнопок показывается рамка «Подмена временно приостановлена»,
> пояснение о восстановлении интеграции и заморозке времени действующего доступа.
> Аккаунт доступен; после завершения сбоя кнопки возвращаются автоматически.
> Работает без входа и без вкладки Яндекса через публичный config; обычная потеря сети не объявляет сбой.
> [Решение и точный текст](../decisions/INCIDENT-POPUP-2026-10-11.md).
> [CI/MySQL/Chromium PASS](https://github.com/manufact-test/nomusic/actions/runs/38152299457): 168 клиентских тестов;
> реальная HTML/CSS геометрия и скрытие кнопок проверены в Chromium при ширинах 340/560 px.
> [Настроенная сборка PASS](https://github.com/manufact-test/nomusic/actions/runs/38152296098).
> Полный ZIP CELIKOM-0.4.24-full.zip: 2439236 bytes,
> SHA256 `c747e11f266c180ea4153aeeb9f35905d8a1e06d46876eb03019f1a4c1bff9d3`.
> Live сервер остаётся `0.4.23-df8bd247b9ae0a6ff1ecc75f453403fa84be8529`;
> backend deploy, миграций и объявленного live incident для этой правки нет.
> Ручная приёмка нового клиентского экрана владельцем ожидается; реальный сбой ради UI-теста не включать.
> Реальная платёжка отсутствует: замораживается время доступа, не деньги.
> Этапы 11/12 и коммерческие зависимости 13 частичные; PR #6 OPEN/unmerged, Issue #7 OPEN.

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

> **Контрольная точка 11.10.2026 — 0.4.21 принята владельцем.**
> Подтверждение «да отлично все работает!)» закрывает ожидание проверки цвета иконки
> и финальных UI. Этап 10 закрыт; этапы 11/12 остаются частичными, реальной оплаты нет.
> Автоматические проценты за approve и перенос приняты; срок начинается от оплаты,
> до неё новые начисления не сгорают. Применение/расходование скидки и paid referrals
> ещё не подключены. Следующий независимый пакет — этап 13, пока не начат.
> Полная актуальная передача: [CHECKPOINT-2026-10-11.md](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/decisions/CHECKPOINT-2026-10-11.md).
> Эта запись имеет приоритет над историческими ожиданиями ниже. Не повторять принятую QA.

> **11.10.2026 — клиент 0.4.21: исправлена причина постоянно серой иконки.**
> Владелец подтвердил остальные UI правки 0.4.20; цвет иконки до этой правки
> не работал в его реальной установке. Причина: относительный путь assets/icons
> из MV3 background/service-worker.js разрешался как background/assets/icons,
> а setIcon error скрывался и состояние ошибочно считалось применённым.
> Путь теперь /assets/icons, shown записывается после успешного setIcon; ошибки
> диагностируются и следующий heartbeat повторяет попытку. Очередь сохраняет Stop
> при быстром Start/Stop, повторные heartbeat не вызывают лишней перерисовки.
> [CI 38145679653 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38145679653):
> 156 тестов расширения, 17 прототипа, PHP/MySQL и Chromium playback/disclosure.
> Новые тесты разрешают URL от вложенного worker, читают реальные PNG 16/32/48/128,
> проверяют их размеры и RGB серого/зелёного фона; проверяют повтор после setIcon error.
> Это проверка файлов/путей и контроллера, а не наблюдение toolbar на ПК владельца.
> Семантика прежняя: enabled + разрешённый доступ + здоровая связь с Яндексом = green,
> независимо от замены песни. Gray при Stop/logout/потере связи. Палитра сохранена.
> Изменения только клиента, сервер остаётся 0.4.20-86484d2217b7261daec10ec3976ad1c74e5c25a3;
> новые deploy/миграции/сброс аккаунтов не выполнялись, PR #6 OPEN/unmerged.
> Полный CELIKOM-0.4.21-full.zip сохранён, 2435327 bytes, SHA256
> 6139df6bd1ae305fd5f06adf41d48e94adf8f59c662429c94447b3a5a0efb0c8.
> Заменить файлы текущего расширения, Reload и обновить Яндекс Музыку один раз.
> Ручное подтверждение смены цвета в установке владельца пока ожидается.

> **11.10.2026 — 0.4.20 развёрнута, завершающие UI правки проверены.**
> Владелец явно разрешил GitHub публикацию и обновление админки. Рабочая ветка
> feature/api-range; PR #6 OPEN/unmerged, issues #7/#13 остаются открыты.
> Зелёная C означает включённый CELIKOM со здоровым подключением к Яндекс Музыке
> после проверки доступа; наличие замены у песни не влияет на цвет. Stop/logout,
> потеря связи и закрытие вкладок возвращают светло-серую C. Permissions прежние.
> Нижняя повторная подсказка входа удалена; раскрытие и красный border аккаунта сохранены.
> Сворачивание истории сохраняет viewport даже у конца страницы; временно резервируется
> только недостающая высота, освобождаемая при прокрутке вверх. Под кнопкой отступ 16px.
> Native Chromium проверяет реальную геометрию при закрытии и повторном toggle;
> событие scroll для очистки резерва отправляется явно из-за virtual-time режима.
> [CI 38144748585 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38144748585)
> и [финальный CI 38145051899 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38145051899):
> 154 теста расширения, 17 прототипа, 5 disclosure сценариев, PHP/MySQL, Chromium playback.
> [MariaDB 38144565856 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38144565856).
> [Snapshot 38144565834 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38144565834):
> 33 таблицы и 12 аудио; [изолированное восстановление 38144647843 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38144647843).
> [Deploy 38144891279 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38144891279),
> release 0.4.20-86484d2217b7261daec10ec3976ad1c74e5c25a3; HTTPS и повторные миграции прошли.
> [Private audit 38145048452 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38145048452),
> [reward history audit 38145048509 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38145048509):
> аккаунты/devices/sessions/trials/catalog/media/policy/ledger/allocations сохранены.
> Новых миграций нет, правила наград владельца сохранены; реальная оплата отложена.
> Полный CELIKOM-0.4.20-full.zip сохранён, 2435273 bytes, SHA256
> 373225e2d402108c00530ac0c77d072ccb2d3715333fdefac5b5d75b4792369f.
> Если 0.4.20 уже установлена, обновить только страницу админки. Иначе заменить файлы
> текущей установки, Reload расширения и обновить Яндекс Музыку. Прежние загрузки и
> бонусы уже приняты; ручной просмотр нужен только для оставшихся UI правок.

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

> **11.10.2026 — уточнение владельца: автоматические бонусы, пакет 0.4.17.**
> Одобрение уникальной версии сразу начисляет автору бонус, без второго решения.
> Настройки: процент за песню, максимальная скидка за календарный месяц UTC,
> срок действия после оплаты. Сохранить включает автоматические начисления,
> Изменить открывает настройки. Обязательные причины, ручное начисление и лимит
> количества наград удалены из интерфейса. Аудит пишется системой автоматически.
> Избыток не теряется: 7 песен по 3% при пределе 20% дают 20% текущего месяца
> и 1% следующего. При больших объёмах очередь распределяется по следующим месяцам.
> По ответу владельца срок начинается **от оплаты**: до подтверждённого платежа
> у новых автоматических бонусов нет expires_at. Неиспользованный запас сохраняется.
> Миграция 013 добавляет reward_allocations и отличает новые автоматические бонусы
> от исторических ручных; миграции 011/012 и прежние grants не изменяются.
> Изменение процента/срока не переписывает начисленные бонусы. Текущий общий предел
> ограничивает доступный для будущей оплаты запас. Исторические pending без награды
> не backfill: новая ставка относится к новым одобрениям после настройки.
> В аккаунте показаны начисленные проценты и перенос без ложного paid entitlement.
> Платежи, привязка расхода к платежу, повторная оплата в одном месяце, возвраты
> и защита повторного использования требуют отдельной интеграции #12. До неё
> это учёт бонусов, не реальная скидка в checkout. Этап 12 не закрывается.
> Ручная проверка 0.4.16 со вторым одобрением отменена как устаревшая.
> Код готовится и проверяется; rollout и ручная приёмка ещё не подтверждены.

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

> **11.10.2026 — подготовлен функциональный пакет наград 0.4.16.**
> [CI 38129250332 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129250332),
> код `ddbc192d6855f2187c80f7692176eeb7b50c44fb`: 141 тест расширения,
> 17 прототипа, PHP 8.3/MySQL, 7 evidence + 9 policy/decision сценариев,
> native Chromium. Проверены cap/stacking, реальные owner POST/CSRF/roles,
> revoke/expiry, audit rollback, два параллельных grant при лимите один,
> повтор миграции после DDL без дублирования колонок/сброса правил.
> Исправлены пойманные до live rollout гонка snapshot при cap и результат
> no-op SQL при повторе миграции. [Snapshot 38129063156 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129063156):
> 8 audio объектов, 24 SQL таблицы и env. [Restore drill 38129248062 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38129248062):
> файлы и SQL восстановлены изолированно, live MySQL не затронута.
> Следом guarded deploy с сохранением всех прежних credentials и flags;
> FEATURE_REWARD_ELIGIBILITY включить отдельным узким переключением после миграций,
> policy оставить выключенной/нулевой до явной настройки владельца в админке.
> Реальной оплаты, расходования бонусов и нового paid entitlement нет. Подробности:
> [план наград](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/test-plans/CELIKOM-STAGE12-REWARDS.md).

> Проверено: код `47fc63055c4070cfe296c6de275b9175f5f40fd9`,
> [CI 38128021136 — PASS](https://github.com/manufact-test/nomusic/actions/runs/38128021136):
> 141 тест расширения, 17 тестов прототипа, PHP 8.3/MySQL, семь сценариев reward
> (включая четыре параллельных процесса), полный серверный регресс и native Chromium.
> [Подробности пакета](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/test-plans/CELIKOM-STAGE12-REWARDS.md).
> Отдельный ZIP владельцу не отправлен; live rollout не выполнялся.

> **11.10.2026 — следующий пакет 0.4.16, ещё не выпущен владельцу.**
> По решению владельца ошибку старта Яндекса пока не расследуем. Ручные проверки
> отдельных текстов/малых UI-правок больше не запрашиваем: следующий полный ZIP
> только вместе с содержательной работающей функцией. В него включить проверку
> отсутствия пустого отступа без трека/вне Яндекс Музыки. Пустая строка версии
> теперь скрывается, известное отсутствие трека восстанавливается синхронно из кэша.
> Продолжен этап 12: миграция 011 и RewardService фиксируют только pending-доказательство
> одобренного вклада в одной транзакции с approve и audit. Автор новых пользовательских
> загрузок берётся из bearer-сессии, поле uploaded_by_user_id сохраняется при создании;
> повторные запросы/новые связи того же файла не меняют автора. Дубликаты, rejected,
> wrong_track, bad_quality, reactivate и owner-only seed не создают новую запись.
> GET /api/v1/rewards возвращает только собственный агрегат, не выдаёт награду.
> FEATURE_REWARD_ELIGIBILITY=0; Hostinger не менялся, старые загрузки не перепривязаны.
> pending означает ожидание политики наград, а не выданную скидку/доступ. Размер,
> MAX_DISCOUNT_PERCENT/MAX_REWARD_PER_MONTH, применение/отмена и админские действия
> — следующий пакет; величина награды по Master v1.5 §17.2 не определена.
> Этапы 11/12 не закрывать. Реальные платежи и квалификация друзей остаются в #12.

> 0.4.15: [CI 38126807827](https://github.com/manufact-test/nomusic/actions/runs/38126807827) — PASS; [приватная сборка 38126804749](https://github.com/manufact-test/nomusic/actions/runs/38126804749) — PASS. 140 тестов расширения, 17 тестов прототипа, PHP/MySQL и native Chromium. Код `e00ae05e5573d1d4376b36bf857ead0cf9bde0eb`. Полный ZIP SHA256 `d0868fb11eb90844d5b34a032f297e580fa42956c5a867af8b1181891a360571`. Ручная оценка отсутствия мигания владельцем ещё не выполнена.

> **11.10.2026 — 0.4.15, стабильные строки доступа и версии песни.**
> Повторное открытие окна синхронно восстанавливает последнее отображение из
> extension-origin localStorage, не ожидая service worker/сеть. При первом открытии
> без данных видны «Загрузка…»; изменение текста плавное, обе строки сохраняют
> высоту. Не переписывать/анимировать одинаковые ответы. Название/статус версии
> привязаны к Track ID, поздний ответ прежнего трека игнорируется. Выход очищает
> положительное отображение; кэш не выдаёт разрешение подмены. Серверные проверки
> доступа не изменены. Hostinger/музыкальная библиотека не менялись.
> Интернет-проверка: Фонтанка 11.10.2026 07:24 сообщает о массовых перебоях,
> включая Музыку: https://www.fontanka.ru/2026/10/11/76693248/ . Dialog.UA
> 11.10.2026 04:38 публикует тот же текст ошибки старта:
> https://www.dialog.ua/russia/vsu-udarili-po-tretemu-data-tsentru-yandeksa-v-rf-posle.html .
> Это внешние сообщения, а не доказательство причины ошибки у владельца;
> официальная status.yandex.cloud доступна только с JS, её текущий статус не подтверждён.
> Владельцу не предлагать проверять заглушки оплаты/приглашений.

> 0.4.14 проверена: [CI 38125856819](https://github.com/manufact-test/nomusic/actions/runs/38125856819) — PASS; [приватная сборка 38125852696](https://github.com/manufact-test/nomusic/actions/runs/38125852696) — PASS. 137 тестов расширения, 17 тестов прототипа, PHP/MySQL и native Chromium. Код `f1dffc87f9ac991fee9133503cbdd34c02bd1922`. Полный ZIP SHA256 `b7a54dd4f1e704065b839bf38ecdad901d139727d00962e13031a3443bc7b6bd`.

> **11.10.2026 — 0.4.14, повторная правка по снимкам владельца.**
> Рамка аккаунта присутствует с первого отображения окна. Последняя подпись
> сохраняется синхронно локально, без почты/токенов и без выдачи доступа;
> выход заменяет подпись на «Аккаунт · войти». Скрыт раздел подписки/друзей,
> пока в нём нет доступных функций. Владельцу не предлагать проверять заглушки.
> Сообщение Яндекса «Не удалось получить часть данных при старте» не создаётся
> CELIKOM; причина у владельца не установлена. Добавлена изоляция ошибок
> наблюдателя fetch/XHR: наблюдение не должно менять ответ или срывать отправку
> запроса страницы. Нужное сравнение — полностью отключить CELIKOM в Chrome
> и открыть Яндекс Музыку заново; «Стоп» в окне не исключает работу мостов.
> Сервер и библиотека песен не изменены, PR #6 и Issue #7 остаются открытыми.

> 0.4.13: [CI 38125119215](https://github.com/manufact-test/nomusic/actions/runs/38125119215) — PASS; [приватная сборка 38125116407](https://github.com/manufact-test/nomusic/actions/runs/38125116407) — PASS. Проверены 133 теста расширения, 17 тестов прототипа и серверная регрессия PHP/MySQL. Код `171b3e977365cbd5cd9527203ec9cff6eccadb0b`. Полный ZIP SHA256 `78c18e5ea5598c6dc9f4a21c79df47cb986192288941ac8c2476dc91e0528eb0`. Ручная оценка плавности/подписей владельцем ещё требуется.

> **11.10.2026 — исправление окна 0.4.13 по ручной проверке владельца.**
> Убраны ложное приглашение войти перед сроком доступа, повтор срока в разделе
> «Подписка и друзья», кнопка «Обновить» и недоступные действия. Последний срок
> хранится только для отображения, привязан к аккаунту; разрешение подмены по-прежнему
> проверяется сервером. Запоздавший ответ после выхода игнорируется. Раздел компактный,
> с плавным появлением содержимого; подпись явно относится к версии песни для подмены.
> Ручная проверка 0.4.13: несколько открытий окна, раскрытие раздела, выход/вход и
> воспроизведение. Сервер Hostinger и музыкальная библиотека не изменены. Этап 12
> остаётся частично выполненным; оплаты и квалификация приглашений отложены в #12.

> Пакет 0.4.12 проверен: CI [38123377513](https://github.com/manufact-test/nomusic/actions/runs/38123377513) — PASS,
> приватная сборка [38123374615](https://github.com/manufact-test/nomusic/actions/runs/38123374615) — PASS.
> Шесть PHP/MySQL-сценариев приглашений, billing/серверная регрессия, 129 тестов
> расширения и 17 тестов прототипа прошли. Новый UI требует ручной приёмки.
> Для регистрации по коду на Hostinger нужен отдельный защищённый rollout миграции
> 010 и FEATURE_REFERRAL_ATTRIBUTION; пока сервер 0.4.11 сохранён.

> Следующий независимый пакет подготовлен: 0.4.12, экран «Подписка и друзья»,
> коды приглашений и привязка нового аккаунта. Этап 12 — [Issue #13](https://github.com/manufact-test/nomusic/issues/13).
> Реальная квалификация оплат/скидки/награды выключены. FEATURE_REFERRAL_ATTRIBUTION=0.
> Hostinger не изменён. План/ограничения: docs/test-plans/CELIKOM-STAGE12-ATTRIBUTION.md.

> Второй пакет этапа 11 опубликован и проверен: приватное чтение подписки и
> финансовый раздел только для владельца, по валютам. CI [38101176015](https://github.com/manufact-test/nomusic/actions/runs/38101176015) — PASS
> для кода `e27c871dfa6689210c0624bce47853609f05ba1b`. FEATURE_BILLING_VIEWS=0 по
> умолчанию. На рабочем сервере не включён. Следующие независимые работы:
> пользовательский экран подписки/друзей и этап 12; квалификация реальными
> оплатами/выдача платёжных скидок остаётся связана с отложенной задачей #12.

> **Решение владельца 11.10.2026: платёжный сервис отложен и не блокирует разработку.**
> Продолжать независимые части этапа 11 и следующие этапы. Не запрашивать выбор
> провайдера повторно до реальной зависимости. Напомнить владельцу перед первым
> реальным платежом/платным запуском, sandbox-проверкой checkout/автосписания или
> выдачей наград за подтверждённые оплаты. Если решение появится раньше,
> владелец сообщит сам. Учёт: [Issue #12](https://github.com/manufact-test/nomusic/issues/12).
> Этап 11 пока частично выполнен; реальная платёжная интеграция не принята.

> Основа этапа 11 проверена: CI [38098981083](https://github.com/manufact-test/nomusic/actions/runs/38098981083) — PASS
> для кода `0ce8751f8e22ef654a582864724c21d5ad273906`. Все 13 сценариев оплаты,
> серверная регрессия, 125 тестов расширения и 17 тестов прототипа прошли.
> Следующий шаг — данные получателя денег и стран покупателей для выбора
> реального провайдера; рабочий Hostinger 0.4.11 не обновлялся.

> Этап 11: первый серверный пакет BillingAdapter / платёжный журнал / оплаченный
> доступ подготовлен изолированно. Проверки и оставшаяся интеграция описаны в
> [CELIKOM-STAGE11-BILLING.md](../test-plans/CELIKOM-STAGE11-BILLING.md).
> Реальные платежи не подключены; для выбора провайдера нужны данные получателя
> денег и страны покупателей.

## 2026-10-11 — Этап 10 принят и закрыт владельцем

Единый CELIKOM0.4.11 принят: реальная подмена, управление воспроизведением, аккаунт, загрузка MP3, отдельное предложение песни, модерация и четыре исправления интерфейса подтверждены владельцем. GitHub CI, одноразовая MySQL, резервная копия, изолированное восстановление, защищённый деплой и сохранность данных PASS. Пробный период —3дня; сессии независимы, срок обновляемой сессии90дней.

По прямому решению владельца две ручные проверки перенесены, а не объявлены выполненными: компьютер+телефон после появления Android и реальное окончание пробного периода. Учёт: [Issue10](https://github.com/manufact-test/nomusic/issues/10). Это решение заменяет прежний запрет закрытия этапа до данных ручных проверок. Текущие решения владельца в админке сохраняются; старые утверждения о статусах#2/#3 являются историческими. PR6OPEN/unmerged, Issue7OPEN.

Следующий этап — [Issue11](https://github.com/manufact-test/nomusic/issues/11): подписка, оплата и автоматическое продление. Разработка самостоятельная до следующего шага, где нужен выбор провайдера или ручная проверка. Первый пакет изолирован от действующего сервера, без реальных списаний и без тестового обхода платного доступа. Пользовательский термин — «пробный период».

## 2026-10-11 — 0.4.11: owner review fixes; Stage10 OPEN

Owner confirmed public upload, moderation and working playback, then authorized four fixes: admin input focus, numeric version ordering, accurate popup version presence and proposal/version progress. New unified client0.4.11 is ready; server0.4.11 deployed via38096832455 PASS; ordinary-account HTTPS smoke38097007526 PASS (read-only presence, complete signed MP3 ranges, public contributions, separate devices/logout); preservation audit38097007588 PASS: private env, media and table row counts unchanged. Existing proposal records are retained: default queue contains only those still needing MP3, uploaded/fulfilled history is available through filters. Exact service/Track ID linkage also covers existing uploads. No schema migration, audio replacement, account/session changes or trial reset. Current owner moderation decisions for legacy#2/#3 are preserved; no automated approval. Approved144530503/#1 retained.

125extension +17PoC tests and PHP8.3/MySQL/browser CI38096633131 PASS; private Chrome package38096630320 PASS. Snapshot38096630329 (24tables/7audio) and isolated recovery38096739223 PASS. [Evidence and owner checklist](../test-plans/CELIKOM-STAGE10-0411-ADMIN-POLISH.md). PR6OPEN/unmerged, Issue7OPEN, Issue9OPEN. Update CURRENT extension folder in place, reload extension and Yandex tab; existing account.

## 2026-10-11 — Public Upload/Suggest ON; unified client0.4.10 ready; Stage10 still OPEN

Owner confirmed actual0.4.9 music replacement, switching and seeking on2026-10-10. Return/Stop/logout, final two-device owner acceptance and public forms still await owner checks. On2026-10-11 owner requested unblocking disabled Upload Version / Suggest Song screens. Guarded enable38095162535 PASS: only FEATURE_UPLOADS changed with env backup/rollback and full config comparison; backend stays accepted0.4.9, no media/trial/session changes. Ordinary-user real HTTPS MP3 upload + separate no-file suggestion, duplicate retry/status/pending-only enforcement PASS; random QA records cleaned. Existing approved144530503/#1 and pending799133075/#2,38436680/#3 untouched.

Client0.4.10 improves contribution preflight from5 to3 requests (onecurrent-session check; entitlement/config parallel) without caching authorization or exposing refresh credentials. 123extension +17PoC/localCI and fullPHP8.3/MySQL8/nativeChromium CI38095052298 PASS; package38095049548 PASS. [Evidence](../test-plans/CELIKOM-STAGE10-PUBLIC-CONTRIBUTIONS.md). Pre-enable24table/5audio snapshot38094966770 and isolatedrestore38095077520 PASS. Post-enable snapshot38095238280 and isolated recovery38095345800 PASS: config, five audio objects and MySQL restored in isolation; live deployment untouched. Trial stays3days; no repeat reset. Existing accounts preserved.

**NEXT = owner update CURRENT extension IN PLACE to0.4.10**, reload extension AND Yandex tab, existing account. Test a new track without approved/pending version, MP3 upload with rights declaration, independent Suggest Song without MP3, see pending entries in Stage8 admin. Oneclient/oneaccount; no apiTestToken/owner key. Public writes are NOW ON; older OFF statements below are historical. PR6OPEN/unmerged, Issue7OPEN, Issue9OPEN; do not closeStage10 until remaining owner gates pass. Keep original0.4.4 reserve.

## 2026-10-10 — 0.4.8 playback FAIL; working 0.4.4 ZIP compared; 0.4.9 deployed

**Stage10 / Issue9 OPEN, actual Yandex playback NOT accepted.** Owner supplied remote-stream-http diagnostics (track144530503 and bridge healthy). Uploaded ZIP filename says0.4.1, but manifest is0.4.4; byte comparison proves replacement player/controller/sync/original guard identical to0.4.8. Difference lies in legacy test-token versus user-session authorization. Expanded live test exposed transient application503 under load, although the owner's exact HTTP status was not recorded.

0.4.9 reuses one database connection per server request and retries only temporary audio429/502/503/504 at500/1000ms, at most3 attempts; 403 or invalid responses immediately restore original. Safe Diagnostics now include HTTP status, offset and attempts. Core CI122 extension tests + PHP8.3/MySQL8/native Chromium PASS; predeploy24table/fiveaudio snapshot/isolatedrestore and guardeddeployment PASS. Active release `0.4.9-bdd6a70568458d7ef85f1f531ed10bcd9b468579`. [Evidence and limitations](../test-plans/CELIKOM-STAGE10-049-STREAM-RELIABILITY.md).

Next owner gate: update CURRENT extension IN PLACE to0.4.9, reload extension AND Yandex tab, existing account, approved144530503 actual audio and controls/Return/Stop. No new registration/secondprofile needed for this retest. Trial stays3days; existing trial NOT reset again. Original0.4.4 retained, approved/pending unchanged, public Upload/SuggestOFF. PR6OPEN/unmerged and Issue7OPEN. See updated [checklist](../test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Post-deploy integrity38071914225 and complete9-range/two-device HTTPS smoke38071914275 PASS without smoke retries; post-release snapshot38072070059 and isolatedrestore38072152106 PASS. Rollout complete; next is owner actual playback, still pending.

## 2026-10-10 — Owner 0.4.7 playback FAIL; 0.4.8 corrections deployed; trial now 3 days

**Stage10 / Issue #9 OPEN; real playback NOT accepted.** Owner reported no audible replacement and fallback/stopped in 0.4.7. Corrected network-blocking worker heartbeat and forced blank auth-panel height; new regression test passes. Latest owner amendment: trial **3 days**, superseding Master duration. Existing trials backed up and reset; account/password/verified-email/device/session rows and old ledger history retained. Next functional Start creates a new three-day trial. [Patch, limitations and complete evidence](../test-plans/CELIKOM-STAGE10-048-OWNER-FIXES.md).

Active private server `0.4.8-86467ba5e374910c6c7a7f229f3fdbeb958c0729`; full CI, pre/post snapshot/restore, deployment, preservation audit and real HTTPS three-day/session/Range smoke PASS. **Next = owner retests actual 144530503 audio in installed extension updated IN PLACE to 0.4.8**, then Play/Pause/Seek/Next/Return/Stop. Reload extension AND Yandex tab; one enabled CELIKOM in that profile. No new registration; first retest needs no second profile. [Checklist](../test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Do not claim the network-liveness fix proves full live playback.

Original 0.4.4 retained. Approved 144530503/#1 and pending 799133075/#2,38436680/#3 unchanged. replacements/auth/entitlement ON, analytics/public writes OFF. Upload/Suggest remain implemented in SAME client; enable/accept after playback/security gate before closing Stage10. PR #6 OPEN/unmerged, Issue #7 OPEN. Historical 0.4.7/five-day/branch-only instructions below are superseded. Do not repeat the one-time reset or erase accounts.

## 2026-10-10 — Stage10: ONE Chrome 0.4.7 deployed; owner playback gate next

**Stage 10 / Issue #9 OPEN — not accepted or closed.** Normal verified-user session now drives trial → EntitlementService → approved Resolve → session-bound signed Range audio in ONE extension. Five-day trial starts on explicit functional Start, account-level; independent devices / 90-day rolling sessions preserved. Server release `0.4.7-02c4b4f8073b4b76c407b7ed469e2500301ac665`; replacements/auth/entitlement ON, analytics/public uploads OFF. CI, guarded deploy, real two-device HTTPS smoke, integrity audits and pre/post recovery gates: see [rollout evidence](../test-plans/CELIKOM-STAGE10-UNIFIED-ROLLOUT.md).

**NEXT: owner tests actual Yandex playback in clean Chrome profile**, using ZIP 0.4.7, ordinary email login, no apiTestToken and empty test Track ID. [Exact checklist](../test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Keep original installed 0.4.4. Approved 144530503/#1 and pending 799133075/#2,38436680/#3 unchanged. Upload version + separate Suggest song are implemented/tested in SAME client; live FEATURE_UPLOADS stays OFF until playback/security gate, then enable and accept them here before Stage10 closure. No separate final account/playback clients.

PR #6 OPEN/unmerged, Issue #7 OPEN (no proven RangeError fix). Stage9 accepted/closed. No billing or Android live acceptance claimed. Historical blocks below, including “branch only” / “do not start Stage10”, are superseded by this latest state. Do not restart the audit or retire legacy 0.4.4 access before owner acceptance.

## 2026-10-10 — Stage10 STARTED: audit + atomic trial foundation (branch only)

Audited HEAD `8a24929b4aa7bf72b4905a469f0a5d1384f6544b`; incomplete existing scaffolds referenced nonexistent trial columns and had no transactional ledger integration. First safe package adds account_trials + atomic verified-account five-day TrialService, database-clock EntitlementService and hardened bearer scaffold, with disposable MySQL/race/rollback tests in CI. [Audit, boundaries and next package](../test-plans/CELIKOM-STAGE10-AUDIT-ATOMIC-TRIAL.md).

**NOT deployed; unified playback not yet connected.** Existing auth activation remains Stage9-only. User-bearer Resolve, session-bound audio, public Upload/Suggest and clean-install owner playback acceptance remain outstanding. Stage9 is CLOSED; Stage10/Issue #9 OPEN, PR #6 OPEN/unmerged, Issue #7 OPEN. Live read-only config confirms replacements/auth ON, analytics/public uploads OFF. No live catalog/audio/session writes. Original Chrome 0.4.4 preserved. Historical status entries below are superseded by this block.

# CELIKOM — HANDOFF: СТАРТ ЭТАПА 10 (10.10.2026)

**Обязательно начать с этого блока, не с исторических статусов ниже.** Stage 9 **официально принят и закрыт владельцем**. GitHub Issue #8 CLOSED, этап 10 Issue #9 OPEN, план: `docs/test-plans/CELIKOM-STAGE10-UNIFIED-TRIAL.md`.

**Первый шаг следующего чата:** спокойно изучить Master ТЗ MVP v1.5 (новое Приложение I), План работ MVP v1.6 (новый §15), актуальный HEAD `manufact-test/nomusic` ветки `feature/api-range`; затем составить короткий конкретный технический пакет 10.0 и последовательно исполнять. **Не начать с переписывания работающего воспроизведения вслепую.** Нужна общая единая сборка, не отдельная версия регистрации.

**Самое важное требование владельца:** в Stage 10 связать подтверждённую email-авторизацию и trial/entitlement с настоящим API Resolve и MP3 replacement. Сейчас 0.4.4 (оригинальная сохранённая установка) подменяет музыку; 0.4.6 (Stage9) содержит функцию подмены, но в новом профиле отсутствует отдельный `apiTestToken`. `api-broker.ts` и `server/src/Application.php` пока требуют `API_TEST_TOKEN` вместо пользовательской сессии, поэтому самостоятельный вход в аккаунт не включает подмену. **Строгий DoD:** чистый Chrome без тестового токена, email login, 5-day trial, approved song 144530503 подменяется, play/pause/seek/next/return и safe fallback, два devices, upload и Suggest Song, админка без регрессий, CI + Hostinger audits + владелец лично проверил. Этап 10 не закрывать иначе.

**Stage9 закрыт:** user подтверждённые email-коды, пароль восстановлен, дизайн 0.4.6 принят; 90-day refresh deployed [run 38058274439](https://github.com/manufact-test/nomusic/actions/runs/38058274439); integrity [run 38058420995](https://github.com/manufact-test/nomusic/actions/runs/38058420995). Отдельные playback-тесты в 0.4.6 владелец отменил и перенёс на 10. Инструментальные тесты двух Chrome devices есть, APK ещё нет. Stage 8 админка и Stage7 uploads уже приняты.

**Иные обязательные требования:** кнопка «Предложить песню» БЕЗ MP3, БЕЗ галочки о правах на загружаемый файл; существующая админская очередь, антиспам/антидубли; не смешать с загрузкой MP3. Реальная отправка MP3 требует прав и pending/ручную модерацию. Ни одно pending нельзя проигрывать по публичному Resolve.

**Не трогать:** original 0.4.4; PR #6 (OPEN/unmerged), Issue #7 MAIN-world stack overflow (OPEN); approved 144530503/#1 и pending 38436680/#3, 799133075/#2; public upload OFF; private owner token, админку. Не открывать серверный Resolve анонимно. Защита по умолчанию, бэкап/restore/rollback до каждого Hostinger deploy.

**Источник плана:** [Stage10 technical plan](../test-plans/CELIKOM-STAGE10-UNIFIED-TRIAL.md) и [Issue #9](https://github.com/manufact-test/nomusic/issues/9). Следующая коммерческая стадия Stage11 Billing, Android отдельные этапы 16/17; не изменять roadmap.

---
## Этап 10 — ОБЯЗАТЕЛЬНАЯ единая рабочая версия CELIKOM (решение владельца 10.10.2026)

**Жёсткий критерий завершения этапа 10:** больше не должно быть «отдельной рабочей 0.4.4 для подмены» и «отдельной тестовой 0.4.6 для аккаунтов». Собрать и принять **ОДНО расширение** на базе общей ветки, в котором работают все ранее принятые функции этапов 0–9, включая реальную подмену одобренного MP3, Play/Pause/Seek/Next/Return, регистрацию/вход/email-код/recovery, независимые устройства, загрузку/антидубли и админ-модерацию (последняя остаётся в защищённой веб-админке). Не разрабатывать вторую параллельную продуктовую версию.

- Сейчас Chrome 0.4.6 уже содержит движок подмены, **но удалённой библиотеке нужен отдельный `API_TEST_TOKEN`** (`extension/src/api/api-broker.ts` / `server/src/Application.php`). При новом профиле Chrome тестовый токен не переносится, и вход по email **не даёт разрешения на Resolve**. Это объяснение — подтверждённый анализ исходников; конкретная ошибка владельца без live diagnostic не доказана. Нынешний корректно защищённый API нельзя открывать анонимно.
- В этапе 10 реализовать **единое правило доступа `user session + entitlement/trial policy → authorized catalog resolve → signed HTTP Range MP3`**. Обычный пользователь входит по email/паролю один раз, дальше токены обновляются автоматически на устройстве; **не вводит отдельный технический read-only код**. Текущий `API_TEST_TOKEN` оставить только как временный ограниченный технический механизм на переходе, затем убрать из пользовательского сценария. Разные устройства с собственными сессиями не мешают друг другу. Дальнейшие платёжные сценарии применять согласно авторитетному ТЗ/плану, не обещая их готовность заранее.
- Не удалять или не ломать рабочую 0.4.4 до owner-подтверждения единой сборки. Пользователь явно разрешил **не повторять сейчас музыкальные ручные тесты в финале этапа 9**; тесты объединённой подмены являются обязательным acceptance gate именно этапа 10.
- **Обязательная приёмка этапа 10:** чистая установка единого расширения (без `apiTestToken`), вход по подтверждённому аккаунту с разрешённым правом доступа → проверенный одобренный Track ID `144530503` подменяется, Pause/Seek/Next/Stop/Return работают; pending/nonapproved остаются оригинальными; email/recovery не регрессируют; второй профиль/устройство не отбирает сессию; при потере доступа или связи — безопасный возврат к оригиналу; старые аудиофайлы, SHA, флаги и очередь модерации сохранены; нет публичного обхода доступа; CI+реальная ручная проверка владельца PASS.
- Также в этапе 10 обязательно публичное действие **«Предложить песню» без MP3 и декларации прав на загружаемый файл**, рядом с «Загрузить версию», с точным Track ID, rate-limit и антиспамом. **Не объявлять этап 10 закрытым, пока нет единой работающей сборки.**
- `PR #6` OPEN/unmerged; `Issue #7` OPEN. Никакого запуска нового платного режима или изменений живой библиотеки только ради этой записи. Пользователь отдельно запросит документ; **не редактировать мастер-DOCX без конкретного запроса**.


## Этап 9 — финальные правки 0.4.6 готовы, ожидание ручной приёмки (10.10.2026)

Финальный пакет [Issue #8](https://github.com/manufact-test/nomusic/issues/8) реализован в `feature/api-range`:
- Адрес: `name="username"` и `autocomplete="username"` для Chrome, плюс **явный выбор последнего использованного email CELIKOM**, сохраняемого локально без паролей и токенов. Нативный менеджер Chrome может быть ограничен; вручную проверить ввод/выбор (мышью, стрелки/Enter) и вставку.
- Заголовок `Аккаунт` / `Аккаунт · подключён` — белый. Для длинных auth-форм выделена стабильная внутренняя прокрутка и сброс scrollTop только при смене состояния. Одинаковые SVG-глазики на входе и восстановлении.
- При временной потере связи локальная учётная запись не стирается; интерфейс показывает `Аккаунт · нет связи`, не выдавая ложного подтверждения сессии.
- **90 дней скользящей неактивности** вместо 30: новые refresh-токены продлевают срок при реальном успешном обновлении; каждый девайс имеет собственную сессию; logout/revoke/reset по-прежнему работают.
- Версия **Chrome extension 0.4.6**: [приватная Actions-сборка PASS](https://github.com/manufact-test/nomusic/actions/runs/38057989522), SHA-256 `a0fc68a92f1622d195a2e974ddeb940d1f8652720fb693557909b2ebbe238fc2`. [Full CI PASS](https://github.com/manufact-test/nomusic/actions/runs/38057992590) и [серверный CI PASS](https://github.com/manufact-test/nomusic/actions/runs/38058278438).
- **Сервер 90 дней развёрнут на тестовом Hostinger**: [deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/38058274439). Перед ним: [снимок 22 таблиц/5 MP3 PASS](https://github.com/manufact-test/nomusic/actions/runs/38058096988) и [изолированное восстановление PASS](https://github.com/manufact-test/nomusic/actions/runs/38058174200). После него [read-only аудит PASS](https://github.com/manufact-test/nomusic/actions/runs/38058420995); принятый #1 и ожидающие #2/#3, приватное аудио, admin/owner flags без изменения.

**Этап 9 ЕЩЁ НЕ ПРИНЯТ владельцем:** новая 0.4.6 требует ручной проверки UI/paste/autocomplete/плавности глазиков и краткого ретеста Start/Stop/Return; Issue #8 остаётся OPEN. **PR #6 остаётся OPEN/unmerged, Issue #7 OPEN**, Chrome 0.4.4 не заменять; этап 10 пока не начинать. Публичные загрузки OFF.


## ФАКТИЧЕСКИЙ СТАТУС 10.10.2026 — подтверждение email развёрнуто

После подтверждения владельцем получения тестового письма на Proton был развёрнут тестовый email-auth backend: PHP release `0.4.5-bffd2c93df1ac0d3a45de385197a4c51b7c5df94`, миграция 005 `user_email_security`, отправитель Gmail SMTP в приватном Hostinger env. [Deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/38054935718), [on-host integrity audit PASS](https://github.com/manufact-test/nomusic/actions/runs/38055294402), [post-deploy snapshot 22 tables+5 audio PASS](https://github.com/manufact-test/nomusic/actions/runs/38055393728), [isolated restore PASS](https://github.com/manufact-test/nomusic/actions/runs/38055485798). Частный Chrome ZIP 0.4.5 с почтовыми формами: [GitHub artifact](https://github.com/manufact-test/nomusic/actions/runs/38055111493), SHA256 `a3812e53678b27d2fa07a1f6f145dabb1bad7717ba5d37024cff7257b6d0835c`.

**Следующее:** владелец должен проверить в отдельном Chrome-профиле вход ранее созданным email (получение 6-значного кода), восстановление пароля, экран после повторного открытия popup и плеер. Реальная отправка кодов из backend-методов требует этой ручной приёмки; предыдущий тест подтвердил только SMTP. Старые не подтверждённые аккаунты нельзя автоматически доверять. **НЕ ЗАКРЫВАТЬ Stage9 / Issue #8**, PR #6 и Issue #7 оставить открытыми, Chrome 0.4.4 не трогать, Stage 10 не начинать.

## АКТУАЛЬНО 10.10.2026 — Stage 9.1: обязательное подтверждение email

Владелец подтвердил: email verification шестизначным кодом, password recovery, НЕ подтверждать каждое устройство, убрать «Мои устройства» из компактного popup, но сохранить backend revoke. Код и аддитивная таблица `005_email_security.sql` созданы в ветке `feature/api-range`, тесты Disposable MySQL+Chrome пройдены. См. [спецификацию](../deployment/stage9-verified-email.md) и [Issue #8](https://github.com/manufact-test/nomusic/issues/8).

**BLOCKER: реальные SMTP-учётные данные и домен отправителя не предоставлены. НЕТ реальной отправки писем, нового server deploy и формальной приёмки Stage9.** Старые аккаунты в будущем релизе должны подтверждать почту. Текущую Hostinger 0.4.5 с предыдущим экспериментальным API и рабочую Chrome 0.4.4 не трогать до согласованного rollout с резервной копией/откатом. PR #6 и Issue #7 открыты, публичные uploads OFF, Stage10 не начат.

# CELIKOM — актуальная передача в новый чат

## АКТУАЛЬНО: этап 9 — тестовая авторизация включена, ожидается приёмка UI (10.10.2026)

**Status: code implemented, Hostinger 0.4.5 deployed, backup/recovery PASS; Stage 9 not yet formally accepted.** Current release `0.4.5-43bf308f1514881dbe996e7e08650d6e74214cdf`. The user API is now **enabled in the private Hostinger test environment (`FEATURE_USER_AUTH=1`)** with explicit owner authorization on 10.10.2026. The public test-domain endpoint can accept registrations; email ownership verification and password recovery are NOT implemented, so this is not a production/public launch. Existing API owner token, admin sessions, playback, audio and public upload flags are preserved.

Built: additive MySQL migration `004_user_identity.sql` (five new tables: users, user_devices, user_sessions, user_auth_attempts and user_auth_events), Argon2id/bcrypt user-password KDF, hashed opaque access/rotating refresh tokens, refresh replay revocation, device binding and per-device logout/revoke, throttled registration/login, disabled user denial; separate admin auth; auth endpoints /api/v1/auth/{register,login,refresh,logout,me,sessions,sessions/revoke,activate}, extension installation UUID and IndexedDB-held credentials; Stage 9 account UI and real new/first/active/returning metrics. No account tokens sent into Yandex page, logs or `chrome.storage.local`; no trial or billing stage activated.



**10.10.2026 Stage 9 Chrome 0.4.5 acceptance build:** fixed auth-broker transient offline behavior (do not refresh unless access token was actually rejected). Added unit coverage for network outage and explicit 401 rotation, PHP integration coverage for simulated access-token expiry. [Full CI PASS](https://github.com/manufact-test/nomusic/actions/runs/38036595068), [owner-only Hostinger-targeted Chrome package PASS](https://github.com/manufact-test/nomusic/actions/runs/38036567598), independently SHA-256 checked final ZIP `56e87a739b1b7241c11d7702217619e66e3a2d32b8e69104676e5fa1580074d2`. Browser owner checklist: [docs/test-plans/CELIKOM-STAGE9-CHROME-ACCEPTANCE.md](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/test-plans/CELIKOM-STAGE9-CHROME-ACCEPTANCE.md). Server remains running previously deployed 0.4.5 with `FEATURE_USER_AUTH=1`; no redeploy / data or audio mutations. **Still needs owner physical Chrome acceptance; Stage 9 not formally closed.**

**10.10.2026 Stage 9 test activation:** owner approved enabling test-domain registration. A mismatch in the SSH-staged request basename was corrected. [Protected enable and two-device HTTPS end-to-end smoke PASS](https://github.com/manufact-test/nomusic/actions/runs/38034929824): registration, credential validation, second independent installation, rotated refresh, revoked remote session, logout, anonymous resolve/admin audio denial, verified approved #1 audio hash and pending #2/#3, private environment backup with 0600 permissions. Temporary synthetic account cleaned from MySQL. No new deployment or Chrome 0.4.4 changes. **Stage 9 NOT formally accepted yet.**

Evidence: [Chrome private build](https://github.com/manufact-test/nomusic/actions/runs/38000772154) PASS, [guarded Hostinger deploy with full CI](https://github.com/manufact-test/nomusic/actions/runs/38001076778) PASS, [pre-deploy snapshot](https://github.com/manufact-test/nomusic/actions/runs/38000819463) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/38000923973) PASS; [post-deploy independent database/audio audit](https://github.com/manufact-test/nomusic/actions/runs/38001265857) PASS; [21-table + five-audio snapshot](https://github.com/manufact-test/nomusic/actions/runs/38001376977) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/38001474957) PASS. All three protected replacements retain their original states; no music moderation decisions made. CI of core code [PASS](https://github.com/manufact-test/nomusic/actions/runs/38001081205).

**Remaining Stage 9 gate:** owner manual review of Chrome 0.4.5 in a separate profile (account popup UX and two independent physical browser profiles; check post-15-minute refresh), continued security review of public reachable test registration and account recovery. Server HTTPS smoke for register/login/refresh/two devices/revoke/logout already PASSED on Hostinger. Account status administration and long-term email recovery/verification need separate deliberate scope decisions; do not claim them completed. **Do not start Stage 10 yet.** PR #6 OPEN/unmerged, Issue #7 OPEN. Mandatory Stage 10 public `Предложить песню` beside `Загрузить версию`: exact Track ID, NO MP3 or audio-rights checkbox. See `docs/deployment/stage9-auth-rollout.md`.

> **АРХИВ ПЕРЕДАЧИ ЭТАПА 8:** Следующий текст описывает состояние ДО реализации Stage 9. Актуальный Status Stage 9 — в разделе выше.

## Архив: Stage 9 первоначальная точка старта (до реализации)

Stage 8 DONE / owner accepted. Last cosmetic polish removed the duplicate `Выберите причину` placeholder from the rejection dropdown choices while retaining it as the initially displayed prompt. `selected disabled hidden` plus `option[hidden]` scoped custom-picker CSS. [CI PASS](https://github.com/manufact-test/nomusic/actions/runs/37996852645), [16-table+5-audio backup](https://github.com/manufact-test/nomusic/actions/runs/37996978409), [isolated recovery](https://github.com/manufact-test/nomusic/actions/runs/37997098934), [protected deploy](https://github.com/manufact-test/nomusic/actions/runs/37997208947), [original media and DB integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37997432216) PASS. Active release `0.4.4-495351f7697c2865e92053ffe860e426c6e96842`. No real song moderation or mapping changes.

Owner requested a **new chat to START Stage 9** after these master updates. NEXT task is **Accounts + Devices**; NOT Stage 8. Read Master TZ MVP v1.5 Appendix H and Work Plan MVP v1.6 §14/«Этап 9 — Аккаунты + устройства» (updated 10.10.2026). Audit actual `feature/api-range` HEAD and existing authentication/DB first; design additive `users`, `user_devices`, `user_sessions`, hashed KDF credentials, opaque refresh/access tokens; endpoints register/login/refresh/logout/me; extension installation UUID and secure token storage; two-device behavior, session revocation, disabled users, privacy/rate-limit tests, staged Hostinger rollout. No billing/trial/public release yet. Keep admin owner auth separate from user auth.

**Critical:** PR #6 remains OPEN and not merged. Issue #7 MAIN-world RangeError remains OPEN; Stage 6.7 independent Chrome profiles never declared accepted. Protect approved #1 (Track ID 144530503), real pending #3 (38436680, «Вспышка»), synthetic pending #2 (799133075), and functioning original extension. Public uploads OFF. Stage 10 must include separate public **«Предложить песню»** beside **«Загрузить версию»**, NO MP3 upload or rights checkbox for a suggestion; Stage 8 admin suggestion queue already exists. Don't lose requirement in Stage 9 planning.

## Final Stage 8 closeout — 10.10.2026

**STOP development now; no Stage 9 code until the user's separate document instructions.** User approved Stage 8 and explicitly waived re-testing. Latest visual polish: rejection select styled with native CSS `appearance:base-select` + `::picker(select)` / `::picker-icon` and fallback, mint selected/hover rows, clean inner focus border instead of former halo. Tested and deployed in `feature/api-range`, active immutable release `0.4.4-6121a91b570e384095d65c9f9562347eb735e967`. [CI PASS](https://github.com/manufact-test/nomusic/actions/runs/37995677448), [backup](https://github.com/manufact-test/nomusic/actions/runs/37995694271), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37995808661), [deploy](https://github.com/manufact-test/nomusic/actions/runs/37995952723), [independent data/media audit](https://github.com/manufact-test/nomusic/actions/runs/37996133162) PASS. No real track moderation performed or audio changed. Stage 8 UI (private admin auth, MP3, suggestions queue, reports, roles, audit, analytics, two-step moderated confirmation, comments, responsive pagination, green UI) **accepted**.

Next user will ask **about project documents**; wait for specifics, then update appropriate project documentation and master DOCX only as asked. Never silently open Stage 9. PR #6 open/unmerged, Issue #7 open, public uploads OFF. Mandatory Stage 10 public `Предложить песню` action remains (NO MP3 upload and NO rights checkbox, separate from `Загрузить версию`). Owner access in Hostinger-private storage must not be exposed in GitHub/chat.

## Latest — Stage 8.7 two-step moderation UX shipped (09.10.2026)

Owner requested: pressing approve/reject must first open a separate confirmation panel; approval has a mandatory rights/audio checkbox and optional note; rejection has a required reason selector (duplicate/wrong track/bad quality/rights/other) and optional note except custom reason requires text. The final confirm button is the only POST. Existing protected moderation transaction and audit semantics preserved; last decision and comment rendered per track and in audit. Implementation deployed at `0.4.4-8fdd303cefff1c25a8a6958ef04b8e5f56e6c500`, [CI](https://github.com/manufact-test/nomusic/actions/runs/37994628141), [backup](https://github.com/manufact-test/nomusic/actions/runs/37994689194), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37994790977), [deploy](https://github.com/manufact-test/nomusic/actions/runs/37994917008), [post-deploy audio/data audit](https://github.com/manufact-test/nomusic/actions/runs/37995105785) PASS. NO real approvals or rejection performed. Next step **owner checks UI manually**; do not declare Stage 8 accepted until owner confirms. PR #6 / Issue #7 remain OPEN; Stage 10 mandatory public `Предложить песню` beside upload stays in roadmap. Do not update master DOCX until a handoff is requested.

## 2026-10-09 latest — Stage 8 mint-green admin UI owner review

The owner approved the Stage 8 dashboard design/refinement. It has been **deployed** to Hostinger in immutable release `0.4.4-1e1460437d3410192802a8c9310ea7e7de9e7cc1`; [gated deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/37990431204), [predeploy full snapshot](https://github.com/manufact-test/nomusic/actions/runs/37989881372), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37990008446), [post-deploy read-only integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37990757090) all PASS. CI with added Admin metadata/paging tests: [37989681564 PASS](https://github.com/manufact-test/nomusic/actions/runs/37989681564). CI and Stage5 audit workflow MySQL image switched from Docker Hub to verified official public ECR mirror after upstream pull failures; test coverage NOT removed.

Design: light background, mint accents matching `#66e0bf` Chrome extension (not exhausting black+neon); Russian status labels, compact header with download/logout, mobile-responsive audio cards; duration min:sec; technical metadata collapsed; 10/25/50 entries with numeric paging and bounded SQL on uploads, requests, reports, and audit. Existing fixture `celikom-ci` displayed as synthetic test item. Old #1 track has no verified artist/title in DB; **do not invent metadata or touch its approved audio**. The owner can use protected `Уточнить название и исполнителя` after verifying Yandex Track ID; audited DB tracks.artist/title change only, CSRF+role/Track ID guarded.

Next: owner opens `https://darkred-camel-588676.hostingersite.com/admin/login`, checks actual UI, filters 10/25/50, sections, private MP3 playback, logout. **Do not click approve/reject/disable on real pending** without actual rights review. Stage 8 owner manual acceptance 8.7 still OPEN. Stage 10 mandatory `Предложить песню` public button remains committed product requirement. PR #6 OPEN/UNMERGED; Issue #7 OPEN. Do not modify master DOCX until next handoff, and do not repeat accepted Stage7 manual tests.

## Current next action: Stage 8.7 owner login/acceptance (not Stage 8 implementation)

Stage 8 code and additive `003_admin_moderation.sql` **deployed** to Hostinger with `FEATURE_ADMIN=1`, `FEATURE_OWNER_REPORTS=0`, public uploads OFF. URL: `https://darkred-camel-588676.hostingersite.com/admin/login`, login `owner`. The generated password is **not** in GitHub or conversation: owner can view it through private Hostinger File Manager/SSH in `celikom/shared/stage8-owner-login-once.txt` (0600, outside public_html). Delete this one-time plaintext copy after successfully securing admin access; SQL stores only password hash. PR #6 still open, Issue #7 still open. Existing owner-upload credential was not rotated.

Verification evidence: [predeploy backup](https://github.com/manufact-test/nomusic/actions/runs/37984859454), [predeploy restore](https://github.com/manufact-test/nomusic/actions/runs/37985091060), [deployment PASS](https://github.com/manufact-test/nomusic/actions/runs/37985244995), [original-audio/config/data audit PASS](https://github.com/manufact-test/nomusic/actions/runs/37985609247), [owner bootstrap / HTTPS login 200 and no-cookie audio 403 PASS](https://github.com/manufact-test/nomusic/actions/runs/37985814317), [16-table postbootstrap snapshot](https://github.com/manufact-test/nomusic/actions/runs/37985992296) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37986120772). These are **automated gates**, NOT owner manual UI approval. Never change the approved #1 replacement or activate real pending #3 or synthetic #2 without explicit rights review.

Owner checks login, two separate queues, authentic pending audio preview, status filters, audit and logout. Prefer using a separately authorized synthetic fixture for status-change workflows instead of moderating the real tracks. Follow [Stage8 acceptance](../deployment/stage8-admin-acceptance.md). After owner 8.7 PASS, close Stage8 and proceed Stage9 in proper order. **Mandatory MVP** Stage10: public `Предложить песню` button beside `Загрузить версию`, NO MP3 and NO rights checkbox, strict current Track ID; backend queue already exists. Do not forget it. User authorized self-directed, guarded technical maintenance/deploys with backup/rollback, not blind irreversible moderation or credential disclosure.



## Что завершено

- **Stage 7 ПРИНЯТ владельцем** по результатам реальной Chrome/Hostinger загрузки и безопасных автоматических тестов; не требовать повторной приёмки косметических правок.
- Сохранена приватная pending запись: **«Вспышка» — Легенды Про, CENTR**, Yandex `38436680`, Replacement **#3**, приватное MP3 6 486 945 байт с подтверждённым hash, `is_active=0`. Есть отдельная CI синтетическая запись `799133075` / Replacement #2 pending; эти записи нельзя одобрять без Stage 8 модерации. Пользователь также показал зелёный результат для «Животные» — Скриптонит; это пользовательское наблюдение, НЕ отдельный DB-аудит.
- Старый approved track `144530503` / Replacement #1, duration 180872ms, сохраняется. Live backend Hostinger `https://darkred-camel-588676.hostingersite.com`; последняя атомарная Stage 7 server-hotfix доставка: [37971964370](https://github.com/manufact-test/nomusic/actions/runs/37971964370) PASS. UI итог: [37976314199](https://github.com/manufact-test/nomusic/actions/runs/37976314199) PASS; CI [37976319421](https://github.com/manufact-test/nomusic/actions/runs/37976319421) PASS; код в ветке `feature/api-range`.
- Баг: Chrome popup полностью раскрывал большую форму, затем менял высоту назад. Исправлено на последнем commit `429000ad49d933a1ffc9fbd8270caab0582176a0`: убрать анимацию `height`, оставить soft opacity fade. Владелец разрешил не делать ещё одну ручную проверку.
- В браузере пользователя был **один оригинальный CELIKOM и три отдельные Stage7 тестовые установки**; пользователь самостоятельно нашёл оригинал, три остальные **удалил**. Не утверждать конкретный Chrome extension ID; он не был достоверно зафиксирован. На временных копиях подмена прежнего approved трека давала «ошибка подмены»; отсутствие персонального read-only API token в новых установках — гипотеза, НЕ доказательство. Оригинальное расширение не удалять/не перенастраивать.
- PR [#6](https://github.com/manufact-test/nomusic/pull/6) **OPEN / UNMERGED**. Issue [#7](https://github.com/manufact-test/nomusic/issues/7) **OPEN**, периодический MAIN-world RangeError/restorePrototypeHooks, первопричина не закрыта. Формальный Stage 6.7 dual-Chrome-profile check не подтверждён, несмотря на фактическую работу подмены.

## ОБЯЗАТЕЛЬНО: «Предложить песню» — часть текущего MVP

Это **новое утверждённое требование, нельзя забыть**. Не подменять им «Загрузить версию».

- Для пользователя при текущей песне Яндекс Музыки: `Загрузить версию` **ИЛИ** `Предложить песню`.
- **Предложить песню**: отправляется точный автоматически обнаруженный service=Yandex / Track ID + артист/название + каноническая ссылка на трек; **не нужно MP3**, **не нужна галочка про права на загруженный файл**; можно предусмотреть необязательный комментарий (например, запикивание).
- Обычный пользователь ничего не должен искать и загружать; **админ видит заявку**, выбирает статус, при возможности находит легально размещаемую версию или права. Никакой автоматической публикации по одной заявке.
- **Stage 8:** реализовать административную очередь заявок и модерацию `track_requests`, дедупликацию/rate-limit/аудит. Stage 7 уже имеет приватный owner-only `POST /api/v1/track-requests` и `track_requests`, это foundation, а НЕ публичный UI.
- **Stage 10:** вывести публичную кнопку `Предложить песню` рядом с пользовательской загрузкой с необходимой auth/entitlement/anti-abuse защитой. Не выпустить MVP без этой кнопки.
- В финальном Stage 10 UX чётко разделять декларацию прав на MP3 (только если файл загружается) и предложение без файла.

## Следующее действие: Stage 8 — admin moderation

Сверить текущий GitHub HEAD и реальные схемы `tracks/audio_assets/track_replacements/upload_submissions/track_requests`; изучить существующий [Stage8 plan](../test-plans/CELIKOM-STAGE8-MODERATION.md) и Master/Plan. Начинать с безопасной модели `admins` / auth / CSRF / audit_log и минимальных очередей **(A) MP3 uploads pending** и **(B) track-only song requests**. Затем карточка с приватным прослушиванием, просмотром Track ID/ссылки, approve/reject/disable с транзакционными гарантиями и аудитом; admin overview по реально доступным данным. До проверенного owner-gate разработки — только CI + disposable MySQL; доступ к живым pending-файлам без разрешения не менять. Не запускать очередной браузерный тест Stage 7.
Не начинать аккаунты, billing, Android. Не мёржить PR #6 и не закрывать Issue #7.

---

## Архив прежней передачи (09.10.2026, ДО ручной приёмки Stage 7)


**Сверено: 09.10.2026.** Этот файл фиксирует факты исполнения; приоритет требований: Master ТЗ MVP v1.5, затем План работ MVP v1.6. Оба файла обновлены в Library /CELIKOM датированными дополнениями. Новый файл передачи: `CELIKOM_HANDOFF_STAGE7_2026-10-09.md` (`libfile_f798ed7dfd4c81918293e9e894d04edd`), план этапа 7: `CELIKOM_STAGE7_PLAN_2026-10-09.md` (`libfile_1a2c915a3c7c8191997ac58a54e48fce`). Канонические Library IDs: Master `libfile_af7d67f2cc848191947f897a5606675c`, Plan `libfile_4841b3eb31f0819186f49ff9c42cfe4b`. План следующего этапа: [Stage 7 uploads / anti-duplicates](../test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md).

## Проверенный результат

Этапы 0–5 приняты в owner-only тестировании. **6.1–6.6 готовы и имеют зелёный CI; 6.7 серверная часть готова, но весь этап 6 НЕ закрыт формально** (нет подтверждения двух независимых профилей Chrome и осталась периодическая ошибка JS). Владельцу после установки hotfix удалось примерно 30 минут пользоваться Яндекс Музыкой без видимых зависаний, подмена работала; полная owner acceptance ещё не доказана.

- [80/80 JavaScript tests, PHP, disposable MySQL и Chromium CI](https://github.com/manufact-test/nomusic/actions/runs/37926905183) — успех, hotfix commit `1d69906aa04cf7704a89eab9342dd5d73ab936e0`.
- [Private Chrome hotfix archive](https://github.com/manufact-test/nomusic/actions/runs/37927113445) — создан, SHA-256 ZIP проверен. Manifest по-прежнему `0.4.4`; установленная сборка имеет более новый код.
- По прямому разрешению владельца: приватный [snapshot](https://github.com/manufact-test/nomusic/actions/runs/37919980695), [проверка восстановления на изолированной MySQL](https://github.com/manufact-test/nomusic/actions/runs/37920125314), [деплой](https://github.com/manufact-test/nomusic/actions/runs/37920299328), [аудит .env/audio/6 таблиц](https://github.com/manufact-test/nomusic/actions/runs/37920496968), [реальный signed HTTP 206](https://github.com/manufact-test/nomusic/actions/runs/37920657691) — всё PASS. Ни файлы, ни активная привязка не менялись.
- Hostinger: `https://darkred-camel-588676.hostingersite.com`, активный серверный release `0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c`; предыдущий `0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d` оставлен для отката. PHP API 0.4.0, replacements ON, analytics OFF.
- В живой библиотеке только согласованная запись: Yandex Track ID **144530503**, Replacement ID **1**, duration **180872 ms**. Аудио и .env находятся в приватном shared, вне public_html. Audio воспроизводится через 512 KiB signed HTTP Range → MediaSource/blob (прямой Hostinger audio.src блокируется CSP). Fail-open возвращает оригинал.
- GitHub `manufact-test/nomusic`, ветка `feature/api-range`, **PR #6 открыт и не слит** (база develop), не сливать без разрешения. Перед работой проверять HEAD. Request `.github/deploy/hostinger-library-request.json` оставлять `{"operation":"validate"}`. Не менять live DB, аудио или сервер без отдельного разрешения. Резервная копия пока у того же провайдера, не offsite DR.

## Особо важно: ошибка не закрыта

[Открытый Issue #7](https://github.com/manufact-test/nomusic/issues/7).

Chrome показал `Uncaught RangeError: Maximum call stack size exceeded` в `player/main-world-bundle.js`. Ранее стек указывал на `celikomObservedHistory`; параллельно пользователь иногда видел неотзывчивую Яндекс Музыку / `Application error` при возврате на давно открытую вкладку. В hotfix 1d69906 исправили обращение перехватчиков History/media/fetch/XHR к изменяемому `nativeHooks` на захват исходной функции + флаг lifecycle; все автотесты прошли.

**Но после очистки Chrome Errors пользователь снова увидел новую ошибку через ~30 минут**, хотя сам сайт и подмена работали нормально. Скрин указывал на `YandexMusicAdapter.restorePrototypeHooks()` (около строки 1044 итогового bundle). Не установлены точные шаги воспроизведения и первопричина, нельзя утверждать, что ошибка исчезла или безвредна. Не делать рискованный фикс без воспроизведения; при повторении собрать полный stack, проверить смену сессий/heartbeat, unmount и влияние внешних wrappers. Наблюдение переносится в этап 7; формальное закрытие 6.7 отложено.

## Работа следующего чата: Stage 7

**Этап 7: загрузки + антидубли**. Подробный порядок и тесты: [docs/test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md](../test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md). Сначала инвентаризация реальных PHP/DB/Chrome файлов, затем небольшими проверяемыми пакетами: pending upload schema → UploadService → SHA-256 dedupe/idempotency → fingerprint statuses → защищённые приватные endpoints → Add version UI → disposable DB/Chrome tests. Использовать существующие `LibraryManagementService`, `StorageAdapter`, `audio_assets` и `track_replacements`, не переписывать их заново.

**Публичные uploads выключены** (`FEATURE_UPLOADS=false` до этапа 10). Любой upload только pending; ручной approve будет в этапе 8; никакая пользовательская загрузка не может автоматически попасть в resolve. Реальная тестовая загрузка, новая запись на Hostinger и публикация требуют отдельного согласия. На этапе 7 не делаем аккаунты, billing, rewards или Android.

Владельца потребуется подключить только **в конце этапа 7 на 10–15 минут**, когда будет готов приватный Chrome ZIP: выбрать текущий Track ID, загрузить MP3, убедиться в pending и распознавании дубля. Не просить приватные токены в чат/GitHub.

## Первое действие в новом чате

Сначала обновить PR HEAD, прочитать мастер-ТЗ §§11–13 и новый Stage7 runbook. Проверить фактическую схему данных, маршруты и текущий popup. Предложить точечный контракт 7.0 и начать реализацию на `feature/api-range` через GitHub только в изолированном CI. Сообщать фактический прогресс. Отдельно отслеживать issue #7. Не начинать с нового браузерного hotfix без диагностических оснований.

**Нельзя утверждать, что Stage 6 полностью принят или что Stage 7 развёрнут в прод.**

## 2026-10-09 — Stage 7.0–7.7 code handoff (newest entry; supersedes earlier NEXT work-order text)

Latest source: `feature/api-range`. The Stage 7 server/private upload + Chrome UI foundation is committed and CI-green; do not confuse that with accepted/deployed. See `docs/test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md` and `docs/project-status.md`. CI: https://github.com/manufact-test/nomusic/actions/runs/37941932390 and https://github.com/manufact-test/nomusic/actions/runs/37942113245 (success). Check latest HEAD and new CI for subsequent documentation commits.

New files: `server/migrations/002_pending_uploads.sql`; `server/src/Application/{UploadService,Mp3Inspector,AudioFingerprintService,DeferredFingerprintService,UploadRateLimiter,TrackRequestService}.php`; `server/tests/uploads.php`; `extension/src/upload/contract.ts`; `extension/tests/upload-contract.test.mjs`. Updated: `server/{src/Application.php,public/index.php,config/app.php,.env.example}`; `server/tests/http.mjs`; `scripts/test-server-foundation.mjs`; `extension/{src/popup/popup.ts,src/shared/messages.ts,popup/popup.html,popup/popup.css}`. Reuse Stage 6 library and private StorageAdapter; pending never resolves.

**Next before owner manual acceptance:** review latest CI, ensure private extension artifact for owner test, prepare a disposable non-live upload API/DB/storage (without enabling uploads on active Hostinger). Test browser UI exact read-only ID, status pending, renamed duplicate and no public Resolve. Fingerprint worker not implemented; do not claim recompressed audio dedupe. Note PHP ini limits must support selected MP3 size in the future private test. Explicit user approval is required for any Hostinger/server/DB change, real upload, new live asset, deploy request, or merging PR #6. Public FEATURE_UPLOADS stays false to Stage 10; private FEATURE_OWNER_UPLOADS defaults off.

**Carry-over issue:** https://github.com/manufact-test/nomusic/issues/7 — intermittent post-hotfix `RangeError: Maximum call stack size exceeded` in MAIN bundle around `restorePrototypeHooks()`. Root cause not reproduced; do not mark fixed or harmless. Stage 6.7 two-Chrome-profile check absent. Keep PR #6 open, main/develop untouched.

## 2026-10-09 — latest Stage 7 safe hardening handoff (supersedes older CI snapshot)

Latest validated CI: [37945005475](https://github.com/manufact-test/nomusic/actions/runs/37945005475), **PASS** with PHP/MySQL, genuine multipart, 4-worker race, FFmpeg-generated *seekable* 2.5-second MP3 and Chromium native decode/seek/play with test-only signed-byte-compatible Range fixture. Earlier intermediate failed CI runs during test fixture iteration are superseded by this full passing run. Latest source remains `feature/api-range`; check current HEAD before further changes.

`Mp3Inspector.durationMs()` now reads the whole MP3 and rejects malformed/truncated/junk tail; `UploadService` saves measured audio duration, validates duplicate metadata and refuses idempotency retries after a pending candidate has been moderated. Independent owner staging setup/manual protocol: `docs/deployment/stage7-owner-upload-acceptance.md`. Any extension artifact produced by default CI with blank `api/config.json.baseUrl` is for automated verification only, **not** usable for owner upload to an HTTPS staging API.

**Next decision:** Owner permission is required before provisioning isolated external staging HTTPS/MySQL (or modifying any Hostinger resource), configuring its owner token, and producing a correctly origin-pinned private Chrome ZIP. Until then, no live uploads, DB migrations or deployment. Stage 7 is technically CI-complete but not manually accepted. Issue #7 RangeError, formal Stage6.7 two-profile gate, and PR #6 merge remain open.
