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
> Локальный финальный клиент: 164/164 теста; дополнительный CI и read-only audit нового release ожидаются.
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
> [CELIKOM-STAGE11-BILLING.md](test-plans/CELIKOM-STAGE11-BILLING.md).
> Реальные платежи не подключены; для выбора провайдера нужны данные получателя
> денег и страны покупателей.

## 2026-10-11 — Этап 10 принят и закрыт владельцем

Единый CELIKOM0.4.11 принят: реальная подмена, управление воспроизведением, аккаунт, загрузка MP3, отдельное предложение песни, модерация и четыре исправления интерфейса подтверждены владельцем. GitHub CI, одноразовая MySQL, резервная копия, изолированное восстановление, защищённый деплой и сохранность данных PASS. Пробный период —3дня; сессии независимы, срок обновляемой сессии90дней.

По прямому решению владельца две ручные проверки перенесены, а не объявлены выполненными: компьютер+телефон после появления Android и реальное окончание пробного периода. Учёт: [Issue10](https://github.com/manufact-test/nomusic/issues/10). Это решение заменяет прежний запрет закрытия этапа до данных ручных проверок. Текущие решения владельца в админке сохраняются; старые утверждения о статусах#2/#3 являются историческими. PR6OPEN/unmerged, Issue7OPEN.

Следующий этап — [Issue11](https://github.com/manufact-test/nomusic/issues/11): подписка, оплата и автоматическое продление. Разработка самостоятельная до следующего шага, где нужен выбор провайдера или ручная проверка. Первый пакет изолирован от действующего сервера, без реальных списаний и без тестового обхода платного доступа. Пользовательский термин — «пробный период».

## 2026-10-11 — 0.4.11: owner review fixes; Stage10 OPEN

Owner confirmed public upload, moderation and working playback, then authorized four fixes: admin input focus, numeric version ordering, accurate popup version presence and proposal/version progress. New unified client0.4.11 is ready; server0.4.11 deployed via38096832455 PASS; ordinary-account HTTPS smoke38097007526 PASS (read-only presence, complete signed MP3 ranges, public contributions, separate devices/logout); preservation audit38097007588 PASS: private env, media and table row counts unchanged. Existing proposal records are retained: default queue contains only those still needing MP3, uploaded/fulfilled history is available through filters. Exact service/Track ID linkage also covers existing uploads. No schema migration, audio replacement, account/session changes or trial reset. Current owner moderation decisions for legacy#2/#3 are preserved; no automated approval. Approved144530503/#1 retained.

125extension +17PoC tests and PHP8.3/MySQL/browser CI38096633131 PASS; private Chrome package38096630320 PASS. Snapshot38096630329 (24tables/7audio) and isolated recovery38096739223 PASS. [Evidence and owner checklist](test-plans/CELIKOM-STAGE10-0411-ADMIN-POLISH.md). PR6OPEN/unmerged, Issue7OPEN, Issue9OPEN. Update CURRENT extension folder in place, reload extension and Yandex tab; existing account.

## 2026-10-11 — Public Upload/Suggest ON; unified client0.4.10 ready; Stage10 still OPEN

Owner confirmed actual0.4.9 music replacement, switching and seeking on2026-10-10. Return/Stop/logout, final two-device owner acceptance and public forms still await owner checks. On2026-10-11 owner requested unblocking disabled Upload Version / Suggest Song screens. Guarded enable38095162535 PASS: only FEATURE_UPLOADS changed with env backup/rollback and full config comparison; backend stays accepted0.4.9, no media/trial/session changes. Ordinary-user real HTTPS MP3 upload + separate no-file suggestion, duplicate retry/status/pending-only enforcement PASS; random QA records cleaned. Existing approved144530503/#1 and pending799133075/#2,38436680/#3 untouched.

Client0.4.10 improves contribution preflight from5 to3 requests (onecurrent-session check; entitlement/config parallel) without caching authorization or exposing refresh credentials. 123extension +17PoC/localCI and fullPHP8.3/MySQL8/nativeChromium CI38095052298 PASS; package38095049548 PASS. [Evidence](test-plans/CELIKOM-STAGE10-PUBLIC-CONTRIBUTIONS.md). Pre-enable24table/5audio snapshot38094966770 and isolatedrestore38095077520 PASS. Post-enable snapshot38095238280 and isolated recovery38095345800 PASS: config, five audio objects and MySQL restored in isolation; live deployment untouched. Trial stays3days; no repeat reset. Existing accounts preserved.

**NEXT = owner update CURRENT extension IN PLACE to0.4.10**, reload extension AND Yandex tab, existing account. Test a new track without approved/pending version, MP3 upload with rights declaration, independent Suggest Song without MP3, see pending entries in Stage8 admin. Oneclient/oneaccount; no apiTestToken/owner key. Public writes are NOW ON; older OFF statements below are historical. PR6OPEN/unmerged, Issue7OPEN, Issue9OPEN; do not closeStage10 until remaining owner gates pass. Keep original0.4.4 reserve.

## 2026-10-10 — 0.4.8 playback FAIL; working 0.4.4 ZIP compared; 0.4.9 deployed

**Stage10 / Issue9 OPEN, actual Yandex playback NOT accepted.** Owner supplied remote-stream-http diagnostics (track144530503 and bridge healthy). Uploaded ZIP filename says0.4.1, but manifest is0.4.4; byte comparison proves replacement player/controller/sync/original guard identical to0.4.8. Difference lies in legacy test-token versus user-session authorization. Expanded live test exposed transient application503 under load, although the owner's exact HTTP status was not recorded.

0.4.9 reuses one database connection per server request and retries only temporary audio429/502/503/504 at500/1000ms, at most3 attempts; 403 or invalid responses immediately restore original. Safe Diagnostics now include HTTP status, offset and attempts. Core CI122 extension tests + PHP8.3/MySQL8/native Chromium PASS; predeploy24table/fiveaudio snapshot/isolatedrestore and guardeddeployment PASS. Active release `0.4.9-bdd6a70568458d7ef85f1f531ed10bcd9b468579`. [Evidence and limitations](test-plans/CELIKOM-STAGE10-049-STREAM-RELIABILITY.md).

Next owner gate: update CURRENT extension IN PLACE to0.4.9, reload extension AND Yandex tab, existing account, approved144530503 actual audio and controls/Return/Stop. No new registration/secondprofile needed for this retest. Trial stays3days; existing trial NOT reset again. Original0.4.4 retained, approved/pending unchanged, public Upload/SuggestOFF. PR6OPEN/unmerged and Issue7OPEN. See updated [checklist](test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Post-deploy integrity38071914225 and complete9-range/two-device HTTPS smoke38071914275 PASS without smoke retries; post-release snapshot38072070059 and isolatedrestore38072152106 PASS. Rollout complete; next is owner actual playback, still pending.

## 2026-10-10 — Owner 0.4.7 playback FAIL; 0.4.8 corrections deployed; trial now 3 days

**Stage10 / Issue #9 OPEN; real playback NOT accepted.** Owner reported no audible replacement and fallback/stopped in 0.4.7. Corrected network-blocking worker heartbeat and forced blank auth-panel height; new regression test passes. Latest owner amendment: trial **3 days**, superseding Master duration. Existing trials backed up and reset; account/password/verified-email/device/session rows and old ledger history retained. Next functional Start creates a new three-day trial. [Patch, limitations and complete evidence](test-plans/CELIKOM-STAGE10-048-OWNER-FIXES.md).

Active private server `0.4.8-86467ba5e374910c6c7a7f229f3fdbeb958c0729`; full CI, pre/post snapshot/restore, deployment, preservation audit and real HTTPS three-day/session/Range smoke PASS. **Next = owner retests actual 144530503 audio in installed extension updated IN PLACE to 0.4.8**, then Play/Pause/Seek/Next/Return/Stop. Reload extension AND Yandex tab; one enabled CELIKOM in that profile. No new registration; first retest needs no second profile. [Checklist](test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Do not claim the network-liveness fix proves full live playback.

Original 0.4.4 retained. Approved 144530503/#1 and pending 799133075/#2,38436680/#3 unchanged. replacements/auth/entitlement ON, analytics/public writes OFF. Upload/Suggest remain implemented in SAME client; enable/accept after playback/security gate before closing Stage10. PR #6 OPEN/unmerged, Issue #7 OPEN. Historical 0.4.7/five-day/branch-only instructions below are superseded. Do not repeat the one-time reset or erase accounts.

## 2026-10-10 — Stage10: ONE Chrome 0.4.7 deployed; owner playback gate next

**Stage 10 / Issue #9 OPEN — not accepted or closed.** Normal verified-user session now drives trial → EntitlementService → approved Resolve → session-bound signed Range audio in ONE extension. Five-day trial starts on explicit functional Start, account-level; independent devices / 90-day rolling sessions preserved. Server release `0.4.7-02c4b4f8073b4b76c407b7ed469e2500301ac665`; replacements/auth/entitlement ON, analytics/public uploads OFF. CI, guarded deploy, real two-device HTTPS smoke, integrity audits and pre/post recovery gates: see [rollout evidence](test-plans/CELIKOM-STAGE10-UNIFIED-ROLLOUT.md).

**NEXT: owner tests actual Yandex playback in clean Chrome profile**, using ZIP 0.4.7, ordinary email login, no apiTestToken and empty test Track ID. [Exact checklist](test-plans/CELIKOM-STAGE10-CHROME-ACCEPTANCE.md). Keep original installed 0.4.4. Approved 144530503/#1 and pending 799133075/#2,38436680/#3 unchanged. Upload version + separate Suggest song are implemented/tested in SAME client; live FEATURE_UPLOADS stays OFF until playback/security gate, then enable and accept them here before Stage10 closure. No separate final account/playback clients.

PR #6 OPEN/unmerged, Issue #7 OPEN (no proven RangeError fix). Stage9 accepted/closed. No billing or Android live acceptance claimed. Historical blocks below, including “branch only” / “do not start Stage10”, are superseded by this latest state. Do not restart the audit or retire legacy 0.4.4 access before owner acceptance.

## 2026-10-10 — Stage10 STARTED: audit + atomic trial foundation (branch only)

Audited HEAD `8a24929b4aa7bf72b4905a469f0a5d1384f6544b`; incomplete existing scaffolds referenced nonexistent trial columns and had no transactional ledger integration. First safe package adds account_trials + atomic verified-account five-day TrialService, database-clock EntitlementService and hardened bearer scaffold, with disposable MySQL/race/rollback tests in CI. [Audit, boundaries and next package](test-plans/CELIKOM-STAGE10-AUDIT-ATOMIC-TRIAL.md).

**NOT deployed; unified playback not yet connected.** Existing auth activation remains Stage9-only. User-bearer Resolve, session-bound audio, public Upload/Suggest and clean-install owner playback acceptance remain outstanding. Stage9 is CLOSED; Stage10/Issue #9 OPEN, PR #6 OPEN/unmerged, Issue #7 OPEN. Live read-only config confirms replacements/auth ON, analytics/public uploads OFF. No live catalog/audio/session writes. Original Chrome 0.4.4 preserved. Historical status entries below are superseded by this block.

## ТЕКУЩЕЕ СОСТОЯНИЕ 10.10.2026 — ЭТАП 9 ЗАКРЫТ, ЭТАП 10 СЛЕДУЮЩИЙ

**Stage 9 / Issue #8 — OWNER ACCEPTED / CLOSED 10.10.2026.** Пользователь подтвердил настоящие шестизначные письма, email verification, восстановление пароля, вход с новым паролем и финальные Chrome UI исправления версии 0.4.6. Серверные 90-day rolling sessions и two-device сессии внедрены, CI/Hostinger backup/restore/readonly integrity gate PASS. **Отдельный live-APK и физический тест двух устройств не заявлены**: многодевайсная логика протестирована серверными интеграционными тестами.

**NEXT = Stage 10 «Trial + EntitlementService» + ОБЯЗАТЕЛЬНОЕ ОБЪЕДИНЕНИЕ ВСЕХ ФУНКЦИЙ В ОДНОМ CHROME-КЛИЕНТЕ.** Только после [Issue #9](https://github.com/manufact-test/nomusic/issues/9) owner acceptance разрешено считать единый релиз готовым. Текущая 0.4.6 содержит и playback код, но обычная email-сессия не разрешает Resolve: нужен отдельный read-only `API_TEST_TOKEN`, который остался в рабочей 0.4.4, но отсутствует в новой установке Chrome. На этапе 10 соединить user auth + 5-day entitlement/trial + approved catalog Resolve + signed Range audio без отдельного тестового кода для обычных пользователей. Владелец **не хочет повторять ручные тесты playback на временных этапах 9**, переносит контроль реальной подмены/синхронизации на 10.6 и требует одну общую версию, а не вечное параллельное тестирование.

В Stage 10 также ОБЯЗАТЕЛЬНО: «Предложить песню» отдельной кнопкой без MP3 и правовой декларации на файл (вместе с загрузкой версии), rate-limit, точный Track ID. [Технический план Stage10](test-plans/CELIKOM-STAGE10-UNIFIED-TRIAL.md). Не начинать Stage 11 Billing или Android.

**DO NOT TOUCH:** Chrome 0.4.4 working installation до unified-release acceptance, approved track 144530503/#1 и protected pending 38436680/#3, 799133075/#2, админку/owner flags, public uploads OFF. `PR #6` OPEN/unmerged, `Issue #7` OPEN (непризнанный закрытым RangeError). Активный Hostinger = test backend, не публичный production release.

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


## Stage 9.1 verified-email rollout — LIVE TEST BACKEND, AWAITING OWNER ACCEPTANCE (10.10.2026)

Owner confirmed real Gmail SMTP test letter received on Proton. Safely deployed PHP/MySQL email verification and reset to **Hostinger test environment**, release `0.4.5-bffd2c93df1ac0d3a45de385197a4c51b7c5df94`, additive migration 005. [Deploy](https://github.com/manufact-test/nomusic/actions/runs/38054935718), [on-host integrity audit](https://github.com/manufact-test/nomusic/actions/runs/38055294402), [22-table+5-audio backup](https://github.com/manufact-test/nomusic/actions/runs/38055393728), [isolated full restore PASS](https://github.com/manufact-test/nomusic/actions/runs/38055485798). Owner-only Chrome 0.4.5 package [built](https://github.com/manufact-test/nomusic/actions/runs/38055111493), SHA-256 `a3812e53678b27d2fa07a1f6f145dabb1bad7717ba5d37024cff7257b6d0835c`. **Owner still needs to confirm user-facing signup/login/resend/reset email codes in Chrome; Stage9 not formally closed.** Owner Chrome 0.4.4 unchanged; PR #6, Issue #7 and Issue #8 remain OPEN. Future separate «Предложить песню» not forgotten, Stage 10 not started.

## Stage 9.1 — verified email and recovery (development only; 10.10.2026)

Owner approved mandatory email confirmation, reset-by-email, no per-device OTP and removal of `Мои устройства` from compact popup. Code added in `feature/api-range`: `005_email_security.sql`, SMTP TLS mail sender with private env, six-digit email challenges, verified-only access/refresh and revoke-all-on-reset; account UI with code/recovery/eye/custom errors. [MVP amendment](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/deployment/stage9-verified-email.md) and [Issue #8](https://github.com/manufact-test/nomusic/issues/8). Current code CI PASS [38040057944](https://github.com/manufact-test/nomusic/actions/runs/38040057944).

**NOT deployed:** no real SMTP sender or DNS configured; no email delivery tested. Existing public-reachable Hostinger remains the previous test account API; do not claim verified accounts or Stage9 acceptance. Chrome 0.4.4 unaffected. PR #6 and Issue #7 open.

# CELIKOM — execution status

## Stage 9 — test auth enabled, awaiting owner UI acceptance (10.10.2026)

**Status: code implemented, Hostinger 0.4.5 deployed, backup/recovery PASS; Stage 9 not yet formally accepted.** Current release `0.4.5-43bf308f1514881dbe996e7e08650d6e74214cdf`. The user API is now **enabled in the private Hostinger test environment (`FEATURE_USER_AUTH=1`)** with explicit owner authorization on 10.10.2026. The public test-domain endpoint can accept registrations; email ownership verification and password recovery are NOT implemented, so this is not a production/public launch. Existing API owner token, admin sessions, playback, audio and public upload flags are preserved.

Built: additive MySQL migration `004_user_identity.sql` (five new tables: users, user_devices, user_sessions, user_auth_attempts and user_auth_events), Argon2id/bcrypt user-password KDF, hashed opaque access/rotating refresh tokens, refresh replay revocation, device binding and per-device logout/revoke, throttled registration/login, disabled user denial; separate admin auth; auth endpoints /api/v1/auth/{register,login,refresh,logout,me,sessions,sessions/revoke,activate}, extension installation UUID and IndexedDB-held credentials; Stage 9 account UI and real new/first/active/returning metrics. No account tokens sent into Yandex page, logs or `chrome.storage.local`; no trial or billing stage activated.



**10.10.2026 Stage 9 Chrome 0.4.5 acceptance build:** fixed auth-broker transient offline behavior (do not refresh unless access token was actually rejected). Added unit coverage for network outage and explicit 401 rotation, PHP integration coverage for simulated access-token expiry. [Full CI PASS](https://github.com/manufact-test/nomusic/actions/runs/38036595068), [owner-only Hostinger-targeted Chrome package PASS](https://github.com/manufact-test/nomusic/actions/runs/38036567598), independently SHA-256 checked final ZIP `56e87a739b1b7241c11d7702217619e66e3a2d32b8e69104676e5fa1580074d2`. Browser owner checklist: [docs/test-plans/CELIKOM-STAGE9-CHROME-ACCEPTANCE.md](https://github.com/manufact-test/nomusic/blob/feature/api-range/docs/test-plans/CELIKOM-STAGE9-CHROME-ACCEPTANCE.md). Server remains running previously deployed 0.4.5 with `FEATURE_USER_AUTH=1`; no redeploy / data or audio mutations. **Still needs owner physical Chrome acceptance; Stage 9 not formally closed.**

**10.10.2026 Stage 9 test activation:** owner approved enabling test-domain registration. A mismatch in the SSH-staged request basename was corrected. [Protected enable and two-device HTTPS end-to-end smoke PASS](https://github.com/manufact-test/nomusic/actions/runs/38034929824): registration, credential validation, second independent installation, rotated refresh, revoked remote session, logout, anonymous resolve/admin audio denial, verified approved #1 audio hash and pending #2/#3, private environment backup with 0600 permissions. Temporary synthetic account cleaned from MySQL. No new deployment or Chrome 0.4.4 changes. **Stage 9 NOT formally accepted yet.**

Evidence: [Chrome private build](https://github.com/manufact-test/nomusic/actions/runs/38000772154) PASS, [guarded Hostinger deploy with full CI](https://github.com/manufact-test/nomusic/actions/runs/38001076778) PASS, [pre-deploy snapshot](https://github.com/manufact-test/nomusic/actions/runs/38000819463) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/38000923973) PASS; [post-deploy independent database/audio audit](https://github.com/manufact-test/nomusic/actions/runs/38001265857) PASS; [21-table + five-audio snapshot](https://github.com/manufact-test/nomusic/actions/runs/38001376977) and [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/38001474957) PASS. All three protected replacements retain their original states; no music moderation decisions made. CI of core code [PASS](https://github.com/manufact-test/nomusic/actions/runs/38001081205).

**Remaining Stage 9 gate:** owner manual review of Chrome 0.4.5 in a separate profile (account popup UX and two independent physical browser profiles; check post-15-minute refresh), continued security review of public reachable test registration and account recovery. Server HTTPS smoke for register/login/refresh/two devices/revoke/logout already PASSED on Hostinger. Account status administration and long-term email recovery/verification need separate deliberate scope decisions; do not claim them completed. **Do not start Stage 10 yet.** PR #6 OPEN/unmerged, Issue #7 OPEN. Mandatory Stage 10 public `Предложить песню` beside `Загрузить версию`: exact Track ID, NO MP3 or audio-rights checkbox. See `docs/deployment/stage9-auth-rollout.md`.

> **АРХИВ ЭТАПА 8 (до начала Stage 9):** Ниже сохранён исторический контекст передачи 10 октября. Актуальный статус Stage 9 — в разделе выше.


**10.10.2026 — final UI correction and Stage 9 handoff:** Placeholder `Выберите причину` now appears only in the closed rejection select, not as a duplicate item in the customizable Chromium popup (`selected disabled hidden` and scoped `::picker(select)` hidden-option CSS). Existing required validation unchanged. [CI PASS](https://github.com/manufact-test/nomusic/actions/runs/37996852645), [pre-deploy 16-table/5-audio backup](https://github.com/manufact-test/nomusic/actions/runs/37996978409), [isolated restore PASS](https://github.com/manufact-test/nomusic/actions/runs/37997098934), [guarded Hostinger deploy PASS](https://github.com/manufact-test/nomusic/actions/runs/37997208947), [read-only original-audio/DB audit PASS](https://github.com/manufact-test/nomusic/actions/runs/37997432216). Live release `0.4.4-495351f7697c2865e92053ffe860e426c6e96842`. No DB/music changes; Stage 8 remains DONE. **Stage 9 NEXT: users, devices, sessions, Auth API; Stage 9 implementation has not started.** Source of authority: Master TZ v1.5 Appendix H, Work Plan v1.6 §14, and the new starter in `docs/handoff/NEXT-CHAT.md`.

**10.10.2026 — Stage 8 final acceptance / development stop.** Browser-native custom CELIKOM mint dropdown for rejection reason (`appearance:base-select` with browser fallback) and quiet inset border focus, no outer neon halo; no JS or backend behavior changes. User explicitly accepted Stage 8 and waived another manual UI review. Verified [full CI](https://github.com/manufact-test/nomusic/actions/runs/37995677448), [16-table/5-audio backup](https://github.com/manufact-test/nomusic/actions/runs/37995694271), [isolated recovery](https://github.com/manufact-test/nomusic/actions/runs/37995808661), [guarded deploy 37995952723](https://github.com/manufact-test/nomusic/actions/runs/37995952723), [post-deploy data and audio integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37996133162) — PASS. Final live release `0.4.4-6121a91b570e384095d65c9f9562347eb735e967`. No songs approved/rejected/disabled; existing admin/owner credentials kept. **Stage 9 NOT STARTED; owner will first request document work.** Required Stage 10 `Предложить песню` public button (no MP3/rights checkbox) preserved. Master DOCX files not edited in this phase.

**09.10.2026 — Stage 8 admin UI improvement deployed:** owner approved the mint-green/light style matching Chrome mint `#66e0bf`. All queues and statuses localized, comfortable top-right controls, responsive cards/player, 10/25/50 selectable bounded paging (uploads/requests/reports/audit), collapsible technical details, explicit synthetic fixture label and CSRF/owner-only audited repair for missing legacy artist/title. Unknown original metadata NOT guessed; private admin can verify on Yandex and fill title without mutating audio or Track ID. GitHub CI [37989681564](https://github.com/manufact-test/nomusic/actions/runs/37989681564) PASS with metadata test; protected on-host [deployment 37990431204](https://github.com/manufact-test/nomusic/actions/runs/37990431204) PASS (official MySQL image via ECR), fresh 16-table + 5-audio [backup 37989881372](https://github.com/manufact-test/nomusic/actions/runs/37989881372) and [restore 37990008446](https://github.com/manufact-test/nomusic/actions/runs/37990008446) PASS; independent [post-deploy original data/audio audit 37990757090](https://github.com/manufact-test/nomusic/actions/runs/37990757090) PASS. Active release `0.4.4-1e1460437d3410192802a8c9310ea7e7de9e7cc1`. Existing private owner upload access preserved; no moderation decisions or media changes. Stage 8.7 **still needs owner UI approval**; PR6 OPEN, Issue7 OPEN.


**09.10.2026 — Stage 8.7 moderation flow polish deployed:** Native two-step `Одобрить` / `Отклонить` disclosures, a separate final confirmation per action, mandatory explicit rights check for approval, optional owner comment for both decisions, rejection category (duplicate/wrong track/bad quality/rights/other, custom text mandatory for other), comment rendered on the replacement card and in immutable audit log. No JavaScript/CSP relaxation or schema migration; old atomic service and role/CSRF/Track-ID safety preserved. [CI PASS](https://github.com/manufact-test/nomusic/actions/runs/37994628141), [private 16-table/5-audio snapshot](https://github.com/manufact-test/nomusic/actions/runs/37994689194), [isolated restore](https://github.com/manufact-test/nomusic/actions/runs/37994790977), [gated deploy](https://github.com/manufact-test/nomusic/actions/runs/37994917008) and [post-deploy integrity audit](https://github.com/manufact-test/nomusic/actions/runs/37995105785) all PASS. Owner UI acceptance still PENDING; do not approve actual pending tracks before verifying usage rights.

| Stage | Итоговый статус на 09.10.2026 | Подтверждение |
| --- | --- | --- |
| 7 — upload/anti-duplicates | **ACCEPTED / OWNER MANUAL PASS** | Рабочий Chrome upload MP3 → pending, точный read-only Track ID, SHA-256 дедупликация, запрет повторной отправки и повторное серверное чтение pending при новом открытии. На Hostinger подтверждена реальная «Вспышка» — Легенды Про, CENTR, Track ID `38436680`, Replacement ID `3`, 6 486 945 байт, `pending`, `is_active=0`, SHA-256 файла проверен. Approved Replacement #1 (`144530503`, 180872ms) не изменён. Деплой/hotfix [37971964370](https://github.com/manufact-test/nomusic/actions/runs/37971964370), UI-сборка [37974445565](https://github.com/manufact-test/nomusic/actions/runs/37974445565), последний косметический фикс [37976314199](https://github.com/manufact-test/nomusic/actions/runs/37976314199), финальный CI [37976319421](https://github.com/manufact-test/nomusic/actions/runs/37976319421) — success. |
| 8 — moderation/admin | **DONE / OWNER ACCEPTED (10.10.2026)** | Закрытый /admin с логином, CSRF, ролями, приватным Range-прослушиванием, раздельными очередями MP3 / «Предложить песню», жалобами, журналом/CSV, реальными агрегатами. Полный [CI](https://github.com/manufact-test/nomusic/actions/runs/37985244995), pre-deploy [backup](https://github.com/manufact-test/nomusic/actions/runs/37984859454) и [restore](https://github.com/manufact-test/nomusic/actions/runs/37985091060), [deployment 003](https://github.com/manufact-test/nomusic/actions/runs/37985244995), [data audit](https://github.com/manufact-test/nomusic/actions/runs/37985609247), [owner provision/HTTPS 200/403](https://github.com/manufact-test/nomusic/actions/runs/37985814317), post-bootstrap [16-table snapshot](https://github.com/manufact-test/nomusic/actions/runs/37985992296) и [restore](https://github.com/manufact-test/nomusic/actions/runs/37986120772) — PASS. 
| 10 — клиентские публичные действия | **ПЛАН** | После account/entitlement gates вывести в popup два независимых сценария: «Загрузить версию» (с MP3 + заявлением о правах) и **«Предложить песню»** (только текущий точный Track ID, название/артист и ссылка на Яндекс Музыку, БЕЗ MP3 и БЕЗ галочки о правах на файл). Server rate-limit, anti-spam и повторные предложения. |

**Обязательное продуктовое решение:** «Предложить песню» является частью MVP, НЕ необязательной идеей и НЕ заменяет пользовательскую загрузку. На Stage 8 админ просматривает заявки и меняет статусы; Stage 10 — публичный UI. Сами заявки **не** приводят к автоматическому поиску/публикации чужого аудио: администратор отдельно проверяет права на размещение.

**Chrome:** во время приёмки существовали четыре распакованные установки версии 0.4.4. Пользователь самостоятельно установил, какая оригинальная, **сохранил её и удалил остальные три тестовые установки**. Идентификатор оригинальной установки НЕ подтверждён, придумывать его нельзя. Тестовые установки могли выдавать «ошибка подмены» из-за отсутствия сохранённого read-only `API_TEST_TOKEN`; это вероятная гипотеза, не доказанный root cause. По отдельным копиям исходную логику playback не признали сломанной. Не просить пользователя повторно устанавливать Stage 7 и не путать read-only API код с owner-upload кодом.

**Carry-over:** периодический MAIN-world `RangeError: Maximum call stack size exceeded` (Issue #7) остаётся предметом наблюдения; формальный independent-two-Chrome-profile Stage 6.7 gate не подтверждён. Не считать проблему решённой и не закрывать issue без воспроизведения/проверки. Fingerprint worker (сходство перекодированных файлов) ещё не реализован; в Stage 7 только очередь/states, SHA-256 — строго побайтовый дубль.


## 2026-10-09 — Stage 8 private deployment completed, owner acceptance pending

Private origin: https://darkred-camel-588676.hostingersite.com/admin/login, login `owner`. Initial password exists **only** in the 0600 Hostinger-private file `celikom/shared/stage8-owner-login-once.txt`, outside `public_html`; do not publish it in public GitHub artifacts or chat. `FEATURE_ADMIN=1`, `FEATURE_OWNER_REPORTS=0`, public `upload_enabled=false`; existing Stage 7 owner upload token preserved unchanged. Latest active release: `0.4.4-ac2b41dd010afef934da2ab8b434e8c0f08048b9`, PHP API 0.4.0. Additive 003 migrated; no production track approval/rejection/disable performed. Existing approved Track ID 144530503/Replacement #1 unaffected; real pending 38436680/#3 and synthetic 799133075/#2 stay pending.

Evidence: pre-deploy [10-table snapshot](https://github.com/manufact-test/nomusic/actions/runs/37984859454) / [restore](https://github.com/manufact-test/nomusic/actions/runs/37985091060), [deploy and migrations](https://github.com/manufact-test/nomusic/actions/runs/37985244995), [unchanged original media/data audit](https://github.com/manufact-test/nomusic/actions/runs/37985609247), [private login bootstrap and anonymous audio 403](https://github.com/manufact-test/nomusic/actions/runs/37985814317), post-deploy [16-table snapshot](https://github.com/manufact-test/nomusic/actions/runs/37985992296) / [disposable restore](https://github.com/manufact-test/nomusic/actions/runs/37986120772). Backup remains Hostinger-only; offsite disaster recovery is not claimed. Initial access credential plaintext was **never uploaded as a public Actions artifact**. Stage 8.7 still requires owner manual login, viewing both queues, logout and authorized private audio preview; do not touch real pending files without separate rights validation.



Updated: 2026-10-09. Requirement authorities are `CELIKOM_Master_TZ_MVP_v1.5` and `CELIKOM_Plan_Rabot_MVP_v1.6`; this file records execution, not a replacement product specification. They supersede master v1.4 and plan v1.5 while retaining their product requirements. Stable document identities and the next-chat handoff are in [handoff/NEXT-CHAT.md](handoff/NEXT-CHAT.md).

| Stage | Status | Evidence / next gate |
| --- | --- | --- |
| 0 — playback PoC | Accepted | Live 0.0.4, 2026-10-07 |
| 1 — production foundation | Complete | Merged foundation and CI |
| 2 — adapter / bridge | Accepted | Owner completed manual 0.2.1 checklist; supplied healthy JSON; CI run 9; merged PR #4 |
| 3 — local playback engine | Accepted by owner, 0.3.2 | Owner reports everything works; final JSON confirms healthy startup/bridge and manual bypass, 3 activations/3 restores. Two earlier binding-change releases remain observations: their causes are not established by this snapshot. This is owner acceptance, not independent evidence of every live scenario. PR #5 merged |
| 4 — API / MySQL / Range audio | Automated gate passed | 0.4.0 config/resolve/signed audio, approved exact-ID catalog, private LocalStorageAdapter, client cache/broker and remote playback, optional deduplicated analytics. CI run 37825005035 passed actual MySQL migrations/catalog/analytics, PHP HTTP byte-exact 200/206/416/HEAD and native Chromium WAV decode/seek/play, with the deployment helpers in the package. PR #6; Stage 5 live limits remain |
| 5 — Hostinger / live MP3 | **Accepted for private testing; live 6/6 + 6/6, recovery and repeat-deploy checks passed** | Owner-confirmed live browser playback with 0.4.4, six functional and six stability tests. Hostinger server release `0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d` (API version still `0.4.0`) deployed with prior private environment and MP3/approved MySQL mapping intact. CI and deployment success [37904158336](https://github.com/manufact-test/nomusic/actions/runs/37904158336); before/after private SHA-256 and six-table row counts [37904416817](https://github.com/manufact-test/nomusic/actions/runs/37904416817); owner-approved signed MP3 206/CORS [37904551511](https://github.com/manufact-test/nomusic/actions/runs/37904551511). Private on-host snapshot including environment, audio and SQL [37903842547](https://github.com/manufact-test/nomusic/actions/runs/37903842547); isolated file restore and disposable MySQL restore [37903962631](https://github.com/manufact-test/nomusic/actions/runs/37903962631). External condition-watch every 6h alerts only on confirmed failure. **Limitations:** snapshot is on the same provider, not an independent offsite disaster-recovery copy; no deliberate outage of live site. PR #6 remains unmerged. [Operations runbook](deployment/hostinger-stage5-operations.md). |

| 6 — shared replacements library | **Technical packages 6.1–6.6 complete; 6.7 server checks PASS; formal owner gate OPEN (issue #7)** | Shared Asset/Track mapping baseline, transactional LibraryManagementService, restricted private CLI and GitHub Actions. [CI gate 37916187759](https://github.com/manufact-test/nomusic/actions/runs/37916187759); [local-only Action 37916327886](https://github.com/manufact-test/nomusic/actions/runs/37916327886); [read-only Hostinger inspection 37916411482](https://github.com/manufact-test/nomusic/actions/runs/37916411482): one Track, one AudioAsset, one mapping; replacements enabled, analytics disabled. No new real tracks/audio, no production DB mutations or extension deployment. [6.5 CI 37917754208](https://github.com/manufact-test/nomusic/actions/runs/37917754208): 75/75 JS tests, PHP TTL contract and disposable MySQL tests pass. Server-driven positive/negative TTL, signed URL margin and controller negative retry guard are implemented in branch only. [6.6 CI 37918863810](https://github.com/manufact-test/nomusic/actions/runs/37918863810): 78/78 JS tests, actual MySQL cross-instance/shared audio/row-lock contention, byte-exact HTTP 206/HEAD/416 and native Chromium signed Range playback pass. 6.7 deployed server-side by explicit owner authorization; [deployment 37920299328](https://github.com/manufact-test/nomusic/actions/runs/37920299328), [data audit 37920496968](https://github.com/manufact-test/nomusic/actions/runs/37920496968), [signed Range 37920657691](https://github.com/manufact-test/nomusic/actions/runs/37920657691). Live approved audio/mapping preserved. [Configured private Chrome build 37920985864](https://github.com/manufact-test/nomusic/actions/runs/37920985864) awaits owner browser verification. [Stage 6 test protocol](test-plans/CELIKOM-STAGE6-SHARED-LIBRARY.md) and [private library runbook](deployment/hostinger-library-operations.md). |

No accounts, user upload flow, moderation admin, billing, Android playback or client release are claimed complete. Stage 7 is READY FOR IMPLEMENTATION ON ISOLATED DATA; public uploads are OFF. Stage 6.1–6.6 implementation is complete and green, but formal Stage 6.7 acceptance remains pending an independent two-profile owner browser gate and resolution/triage of recurring issue #7. Stage 18 privacy/infrastructure gate is mandatory before client release.

Stage 6.7 read-only baseline was reverified: [Hostinger inspect 37919329751](https://github.com/manufact-test/nomusic/actions/runs/37919329751) returned 1 Track, 1 Asset, 1 Mapping, replacements on, analytics off. No live writes.

Next action: Start Stage 7 implementation at safe package 7.0 from [Stage7 runbook](test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md): inventory source, define pending upload schema, strict idempotent owner-only API design and default-off flags. Stage 7 must use disposable MySQL/synthetic media, and public FEATURE_UPLOADS stays false until entitlement Stage 10. Owner's manual browser upload check is only at the end of Stage 7. Keep [issue #7](https://github.com/manufact-test/nomusic/issues/7) open; do not claim Stage 6 acceptance or change live music and deployment requests. PR #6 open/unmerged.

## 2026-10-09 — Chrome History hook recursion hotfix (owner validation pending)

Owner reported three `Uncaught RangeError: Maximum call stack size exceeded` entries in Chrome extension Errors, traced to `player/main-world-bundle.js` `celikomObservedHistory` around line 1044 and intermittent Yandex Music SPA blank `Application error` / frozen page when returning to an old tab. Root cause identified in `YandexMusicAdapter` lifecycle: wrapper used mutable `adapter.nativeHooks[name]` as its native target. If a third-party/Yandex wrapper retained CELIKOM's wrapper through unmount, on remount the registry could point back into the old wrapper chain and recurse. The source also used this mutable-hook pattern for media, fetch and XHR.

Fix [1d69906](https://github.com/manufact-test/nomusic/commit/1d69906aa04cf7704a89eab9342dd5d73ab936e0): each wrapper closes over its immutable original target and has a per-installation `lifecycle.active` flag; retained stale wrappers stay callable but no longer emit snapshots or inspect the network after unmount. Two regression tests reproduce third-party History wrap/unmount/remount and retained fetch/media functions. [CI 37926905183](https://github.com/manufact-test/nomusic/actions/runs/37926905183) green: **80/80 JS** plus PHP/disposable MySQL/native Chromium. [Hostinger-configured hotfix package 37927113445](https://github.com/manufact-test/nomusic/actions/runs/37927113445) assembled with valid ZIP SHA and exact private API origin; no server redeploy. Workflow/last documentation CI [37927119332](https://github.com/manufact-test/nomusic/actions/runs/37927119332) green.

**Next:** owner replaces files in existing unpacked CELIKOM folder, uses Reload in `chrome://extensions`, closes/reopens Yandex Music tabs, clears past Chrome Errors and exercises navigation, tab-background/foreground, play/pause/seek, Stop/Return original. A blank-page error in Yandex is a plausible consequence of History recursion, not conclusively attributed until owner reproduces or confirms gone. Stage 6.7 browser acceptance remains **pending**; do not merge PR #6 or change existing music/DB. Extension manifest version remains `0.4.4` to preserve established unpacked-install identity; the hotfix is distinguished by Git commit and artifact.

## 2026-10-09 — latest owner update and Stage 7 readiness

Owner installed the 1d69906 History/media/fetch/XHR hook hotfix in the existing unpacked Chrome extension and used Yandex Music for roughly 30 minutes with functional replacement and **no visible SPA freezes**. After clearing the old Chrome Errors entries, a **new** `Uncaught RangeError: Maximum call stack size exceeded` was recorded; screenshot highlighted near `YandexMusicAdapter.restorePrototypeHooks()` in generated `player/main-world-bundle.js` around line 1044. No clear reproduction steps; do not claim the new error is harmless or fixed. Track in [issue #7](https://github.com/manufact-test/nomusic/issues/7); root cause unresolved. CI 37926905183 was green (80/80 JS, PHP, disposable MySQL and Chromium) but CI did not reproduce this post-hotfix symptom. Two-profile owner acceptance not documented, so **Stage 6 code complete but formal sign-off withheld**.

**Next stage 7 is authorized for safe development preparation**, not new live uploads. [Stage7 plan](test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md) scopes multipart owner-gated upload, pending-only records, SHA-256 exact dedupe/idempotency, fingerprint processing-status foundation, read-only track identity in Chrome Add version and isolated regression. Later Stage 8 admin approval is required before any candidate could be activated. Keep FEATURE_UPLOADS=false for public users until Stage 10, no new real MP3 without explicit owner consent.

## 2026-10-09 — Stage 7 implementation (branch-only, CI PASS; owner gate OPEN)

7.0 audit completed. 7.1–7.7 upload foundation committed to `feature/api-range`: additive MySQL schema; owner-gated private multipart uploads / track requests; streaming StorageAdapter + SHA-256 exact dedupe; Track → AudioAsset shared mapping; pending-only candidate and retry identity; deferred fingerprint status foundation; Chrome Add version with readonly current Track ID, rights checkbox, MP3 and progress; synthetic-MP3/disposable MySQL and real HTTP multipart regression. Evidence: [CI 37941932390](https://github.com/manufact-test/nomusic/actions/runs/37941932390) and [CI 37942113245](https://github.com/manufact-test/nomusic/actions/runs/37942113245), success. For package-level details, see [Stage 7 test plan](test-plans/CELIKOM-STAGE7-UPLOAD-ANTIDUPES.md).

**Status: implementation green / NOT owner-accepted / NOT deployed.** Public upload flag remains false; private owner upload flag defaults false, requires a separate strong owner token and explicit later setup. No Stage 7 DB migration, upload or new real MP3 has been applied on Hostinger. Existing approved ID 144530503 (Replacement 1), server release `0.4.4-18ba6fc6d98f88e24f75daadb2262e6a66a9ed5c`, and PR #6 remain unchanged in deployment/merge state. Fingerprint computation itself is deferred (processing-state foundation only); Stage 8 manual moderation and Stage 9–10 account/entitlement are not implemented. The client/manual acceptance gate, exact-duration/decode quality review and parallel race stress remain outstanding. Stage 6.7 sign-off still OPEN; [issue #7](https://github.com/manufact-test/nomusic/issues/7) remains unresolved.

## 2026-10-09 — Stage 7 hardening / CI 37945005475

Stage 7 code remains **branch-only, owner gate open, not deployed**. Stronger full-frame MPEG Layer III inspection now measures actual audio duration and rejects partial, corrupt and trailing-payload MP3. SHA-256 candidate metadata is checked against measured duration on asset reuse. Retry after a moderation-state transition is not misreported as pending. Four concurrent uploads from independent PHP workers to disposable MySQL agree on a single pending candidate. CI-only FFmpeg synthesizes a real 2.5-second MP3; test-only PHP byte-range fixture and native Chromium successfully decode, seek and play it.

[CI 37945005475](https://github.com/manufact-test/nomusic/actions/runs/37945005475) **PASS** — JS (83 tests), PHP, disposable MySQL, true HTTP multipart/race, native WAV and synthetic MP3 Chromium, package validation. Owner gate preparation at [stage7-owner-upload-acceptance.md](deployment/stage7-owner-upload-acceptance.md). No live Hostinger DB/schema/audio writes, no stage7 deployment, no public uploads, no stage8 approval. PR #6 open/unmerged; Stage6.7 and issue #7 remain open. Real browser owner test requires an independent HTTPS staging environment and explicit permission to provision it.
