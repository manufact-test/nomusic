# CELIKOM контрольная точка 12 октября 2026 МСК

Последняя контрольная точка имеет приоритет над историческими статусами. GitHub manufact-test/nomusic, feature/api-range; PR6 OPEN/unmerged, не сливать. Этапы0–10 приняты. Этап15 исключён по решению владельца: отдельную Alpha/группу/gate не создавать и не объявлять отменённые тесты выполненными. Этап16 частичный,17 не начат,18 приватизация до выдачи внешним клиентам. Провайдер оплаты не указан;11/12/коммерческие13 частичные, Issues11/12/13 открыты.

## Клиенты и сервер

Владелец принял единое расширение0.4.28 и оформление промокодов. Новое0.4.29 добавляет техподдержку и содержит прежний playback/account/upload/suggest/moderation/promo/reward функционал. Адрес поддержки не выбран: копирование обращения доступно, реальная отправка email не подключена. CELIKOM_SUPPORT_EMAIL задаёт подтверждённый адрес при сборке; никаких предполагаемых адресов, отправки без действия пользователя или дампов токенов. Backend остаётся0.4.28-29802edf4a4c071662639a2eb475915b9bf17bb8; API https://darkred-camel-588676.hostingersite.com. Ночного live deploy не было.

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

Security14 independent code work выполнено ранее; operational backups/restore/log rotation/CVE/capacity остаются отдельными незавершёнными проверками. Issue7 stall cause не доказан; Issue10 real trial expiry и computer+Android deferred/not done. FEATURE_BILLING_VIEWS=0, FEATURE_REFERRAL_ATTRIBUTION=0, FEATURE_REWARD_ELIGIBILITY=1. Сохранить accounts/sessions/devices/trials/entitlements/audio/catalog/moderation/reward policy/ledger/allocations; без reset/backfill, без переписывания применённых миграций. Сохранить Track144530503/Replacement1 и резервную0.4.4. Принятые загрузки/награды/цвет иконки не повторять.

## Ночные проверки и сборки

Android0.3.1 код ab252eb8687045d71bde2a0a8c31820bf5e229f9: workflow38181904506 PASS lint/build и2 API35 native tests, font_scale1.3; общий CI38181907491 отдельно. APK SHA256 faf79d301b06c87de04102dde04cf98d736ef13bdef07c9a3831ca71ab28ad81. Это технические проверки diagnostic harness, не проверка новых полей на телефоне владельца.

Extension0.4.29 код b4668c38a388382c0846c5d22cb6e0f90c6619b0: общий CI38182016479 PASS; configured package38182012384 PASS,178 client tests, native Chromium support copy/mail draft/privacy PASS, security gate52 client files PASS. Полный ZIP SHA2565b1c1d75517ccf739fb7cecd172d4f38fd7ad7398880889ca8e614f478533930. Email fixture team@example.org существует только в изолированном тесте, не является адресом проекта и не встроен в поставку.

Для запуска mail draft требуется реальный адрес владельца: CELIKOM_SUPPORT_EMAIL при сборке. В ночной поставке поле пустое, кнопка email недоступна; копирование обращения работает. Не заявлять подключённый канал писем до настройки mailbox/получателя.
