# CELIKOM контрольная точка 12 октября 2026 МСК

Последняя контрольная точка имеет приоритет над историческими статусами. GitHub manufact-test/nomusic, feature/api-range; PR6 OPEN/unmerged, не сливать. Этапы0–10 приняты. Этап15 исключён по решению владельца: отдельную Alpha/группу/gate не создавать и не объявлять отменённые тесты выполненными. Этап16 частичный,17 не начат,18 приватизация до выдачи внешним клиентам. Провайдер оплаты не указан;11/12/коммерческие13 частичные, Issues11/12/13 открыты.

## Клиенты и сервер

Владелец принял единое расширение 0.4.28 и оформление промокодов. Новое 0.4.30 добавляет «Связь с поддержкой»: сообщение из аккаунта → очередь админки → ответ администратора в CELIKOM и по email. Используется существующая SMTP-почта регистрации (CELIKOM_MAIL_FROM), на неё же отправляется копия нового обращения. Нового выбора адреса не требуется. Миграция 016 аддитивная, существующие доступы и финансовые журналы не меняет. Backend обновлён до release 0.4.30-c9b857776fed0fe80725c64d2091971de9c3583f; итог проверки сохранности и восстановления фиксируется ниже. API https://darkred-camel-588676.hostingersite.com.

Android WebView0.2.0 отклонён владельцем и не является продуктовым решением. Требуется companion уже установленной Яндекс Музыки: её UI/плеер/master-команды, фон/экран выключен/наушники/автомобиль. Диагностические APK не являются отдельными финальными клиентами. Общие account/EntitlementService/catalog должны использоваться будущим Android-клиентом; не вводить отдельное право доступа.

## Подтверждённое исследование

Owned cross-app эксперимент двух собственных UID на Android10/15, без root: исходный ненулевой audio session подавляется DynamicsProcessing, master продолжает идти, альтернатива остаётся слышимой, explicit release возвращает исходный сигнал. Run38177741159 PASS. Это не proof native Яндекса, crash restoration или physical routes.

Владелец проверил0.3.0-probe: HONOR50/NTH-NX9, Android13/API33, Яндекс2026.09.5 #167gpr. Notification listener connected. Яндекс дважды сам вызвал DISPLAY_AUDIO_EFFECT_CONTROL_PANEL, фактический callingPackage=ru.yandex.music и session27489. Конкретный штатный путь передачи сессии на этом устройстве подтверждён. Broadcast OPEN extras остаются claims, не auth; повторные OPEN не доказывают несколько физических аудиосессий. Номер сессии временный, не переиспользовать между запусками.

MediaSession отдаёт title «Девочка», artist kavabanga Depo kolibri, duration271040ms, pause/state2, position2885ms, MEDIA_ID32. Штатная ссылка владельца https://music.yandex.ru/album/1777786/track/36116709 — настоящий ID36116709; MEDIA_ID32 не соответствует ему. Ни title matching, ни слепой числовой MEDIA_ID не включать как exact ID. Скрин-off timeline/history недостаточны для принятия background audio.

Яндекс закрывался и после удаления диагностики; владелец сообщил, что отключение своего VPN вернуло запуск. Это наблюдение владельца, не доказанный root cause. Дополнительно несколько привычных треков показывали невозможность воспроизведения; причина и связь с наблюдателем не установлены. Нужна контролируемая проверка той же песни/того же VPN при отключённом observer, без очистки данных/переустановки Яндекса.

## Следующая ручная проверка

0.3.1-probe расширяет read-only диагностику: current queue item по activeQueueItemId, MEDIA_ID/URI без секретных частей, имена metadata/extras полей и строго разрешённые numeric trackId/mediaId keys. История bounded20, audio events bounded30 с дедупликацией. Не выгружает всю очередь, artwork, raw Bundles, чужие уведомления/credentials. Observer callbacks сохраняются по sessionToken, без unregister/register на каждом notification update. Оригинальный звук не изменяется; INTERNET/microphone/audio settings permissions отсутствуют.

После проверки CI владелец утром устанавливает0.3.1 (ephemeral debug signing может требовать удалить только прежний diagnostic APK), включает listener и штатную панель Яндекса во время playback, делает next/pause/resume/экран выключен30s и присылает новый отчёт + ссылку последней песни. Проверка gain на реальном Яндексе, sync/drift, безопасное восстановление после crash/kill/Original/session close, Bluetooth/AndroidAuto ещё НЕ выполнены. Если exact ID не доступен стандартно, universal automatic native replacement не обещать; не подменять требование WebView и не прибегать к global STREAM_MUSIC mute/root/TLS interception.

## Доступ и сохранение данных

Promo015 реализован независимо от реальной оплаты:100% бесплатный срок добавляется к остатку (7+30=37), forever требует подтверждения owner, owneractivation limit default1 атомарный, account/code один раз, request идемпотентный, audit/revoke и общий EntitlementService/incident freeze. Частичные проценты — скидка на цену, не бесплатные дни; платёжное применение/короткий срок относительно месяца/комбинации ждут определённых правил и провайдера. Forever grant не является payment или paid referral; наградная процентная policy/ledger carry не сокращает его. Выданные owner grants/настройки/ledger не менять.

Incident13 independent принят:CSRF/migration014/UTC elapsed union/immutable base/audit/concurrency; UIpublic config работает без входа, network error не объявляет incident. Real incident для UI не включать; recurring pause/resume и real payments не подключены. UIдаты МСК, внутренние UTC elapsed и применённые миграции не переписывать.

Security14 independent code work выполнено ранее. Для этого обновления выполняются private snapshot, проверка сохранности и isolated restore; регулярность/offsite backup, log rotation, CVE/capacity остаются отдельными незавершёнными проверками. Issue7 stall cause не доказан; Issue10 real trial expiry и computer+Android deferred/not done. FEATURE_BILLING_VIEWS=0, FEATURE_REFERRAL_ATTRIBUTION=0, FEATURE_REWARD_ELIGIBILITY=1. Сохранить accounts/sessions/devices/trials/entitlements/audio/catalog/moderation/reward policy/ledger/allocations; без reset/backfill, без переписывания применённых миграций. Сохранить Track144530503/Replacement1 и резервную0.4.4. Принятые загрузки/награды/цвет иконки не повторять.

## Ночные проверки и сборки

Android0.3.1 код ab252eb8687045d71bde2a0a8c31820bf5e229f9: workflow38181904506 PASS lint/build и2 API35 native tests, font_scale1.3; общий CI38181907491 отдельно. APK SHA256 faf79d301b06c87de04102dde04cf98d736ef13bdef07c9a3831ca71ab28ad81. Это технические проверки diagnostic harness, не проверка новых полей на телефоне владельца.

Extension 0.4.29 был промежуточной сборкой copy/mail draft; владелец уточнил требование до выдачи. Финальная ночная сборка — 0.4.30 с обращениями через админку. Локальные 178 client tests и security gate PASS; PHP/MySQL/MariaDB и native Chromium проверяются CI. Реальная доставка email и новая read-only диагностика на Honor50 требуют утренней проверки владельца. В тестах только изолированные получатели и mail_test_sink.

## Поддержка: правила

API требует активную подтверждённую сессию, но не оплаченный доступ. Доступ к чужим обращениям закрыт. Owner/moderator отвечают и закрывают; viewer не видит поддержку. CSRF, аудит, экранирование, ограничения тела и атомарный лимит 5 новых обращений в час. Повторный запрос с прежним UUID возвращает прежнее обращение и не отправляет второе письмо; изменение тела с тем же ключом отклоняется. Черновик и ключ переживают закрытие popup в session storage. Обращение/ответ сохраняются до SMTP; ошибка/неопределённость отправки не теряет переписку и не вызывает автоматического повторного письма. Backup/restore охватывает обе новые таблицы. Импорт обычных email-ответов через IMAP не подключён: рабочая переписка идёт через CELIKOM/админку, email — копия/уведомление.

Configured extension 0.4.30: код 2b14f3c13433cdf311170e6fef911ac4ee03634e; workflow38183641658 PASS (Chromium send/inbox/privacy/escaping/двойное нажатие, security и API-target ZIP). Файл полный, единый клиент. Новые ticket/message истории доступны с пагинацией, старые сообщения не теряются.

## Итог проверки поддержки

Код 2b14f3c13433cdf311170e6fef911ac4ee03634e: CI38183645111 PASS, MySQL support/API session/RBAC/CSRF/audit/idempotency/hourly cap/escaped text/pagination/mail failure PASS; MariaDB38183641649 PASS. Configured ZIP38183641658 PASS, SHA256 b5724e3854a174019739ab47aebd5d680e080436bd49fb4095c431543e75c878. Deploy/verify38183803526 и общий CI38183806786 используют release c9b8577. Первое подключение SSH оборвалось до миграций, повторный job обновил сервер; публичный config подтверждает настроенный support contact, а anonymous support возвращает401. Реальных обращений/писем тестами не создавали. API health исторически сообщает0.4.0 из config/app.php; это отдельный legacy маркер, не release directory version.

Deploy38183803526 PASS: pre-snapshot, аддитивная016, HTTPS/PHP/MySQL, after-deploy row-count/env/audio audit, свежий private snapshot и isolated file/MySQL restore PASS. Существующие credentials/flags/grants/reward policy/ledger/allocations сохранены; новые support таблицы пусты до ручного обращения владельца. Эта разовая проверка восстановления не объявляет настроенными регулярный offsite backup/rotation или весь этап14.
