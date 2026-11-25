# CELIKOM — единый запуск инфраструктуры релизов FlokiNET (25.11.2026)

> **СТАТУС:** код и CI-публикация подготовлены, проверка на живом VPS и первая приёмка устройств **не выполнялись** в этом чате. Этот документ не является актом ввода в эксплуатацию. Старые Hostinger-клиенты продолжают работать до подтверждённого перехода.

## Правило владельца (обязательно)

- **Одно установленное CELIKOM Windows.** Разработчик делает проверенную *тестовую* сборку, CI публикует её на защищённом `celikom.com`, владелец вручную скачивает и устанавливает поверх текущей. Никакого второго приложения.
- Пользовательская версия **не меняется автоматически вместе с тестовой**. Только после явного «принимаю версию X, выпускай всем» разработчик обновляет декларативный манифест допуска, и root-публикатор независимо сверяет хеш, подписанный манифест и HTTPS.
- **Клиентам Windows** приложение проверяет подписанный HTTPS feed на запуске и периодически (~30 минут), скачивает в фоне и запускает тихую in-place установку только когда Яндекс закрыт и подмена выключена. В коде предусмотрен Supervisor и откат. Нельзя считать реальный old→new доказанным до теста установленного клиента. Закрытую CELIKOM приложение не обновляет само, проверка происходит при следующем запуске.
- **Android A1, старый Android stable, Windows и браузерное расширение — разные каналы.** Не переносить подписи, номера и URL между ними.
- Никогда не выдавать GitHub draft/Actions URL как пользовательскую ссылку. Не делать приватные CI runner root-деплоерами. Доставка и обслуживание должны работать через FlokiNET без новых тарифов.
- Старый Hostinger не отключать до проверенного перехода уже установленного Android 0.3.92; его клиент жёстко обращается к старому домену.

## Состояние подготовки

| Линия | Подготовленный механизм | Публикация/автообновление |
| --- | --- | --- |
| Windows owner | 0.24.56, подписанный P-256 feed, immutable root importer, защищённый latest и URL каждой версии | Автопубликация тестовых релизов после однократной установки; **VPS ещё не активирован** |
| Windows customer | Отдельная подпись+SHA проверка из доверенного immutable owner-store, `.github/release/windows-customer-stable.json`, динамический публичный `/downloads/windows/CELIKOM-Windows-stable.exe` и `/CELIKOM/Windows/Updates/stable/latest.json[.sig]` | `approved:null`, но при первоначальной установке отдельно публикуется **уже принятая подписанная 0.24.55 (seq2)** как база для возврата и автообновления; версия 0.24.56 остаётся тестовой, old→new ещё не испытан |
| Legacy Android owner | Проверенный приватный оригинально подписанный 0.3.94/code95, hash `d43d2dd12dfa6a4cd79094abccabad67080c6f02542cd25edff55b3d36018469`; CI data-only stage `45683010606` успешен | Кандидат ожидает root signer/API/HTTPS проверки. Запланирован `/downloads/android/CELIKOM-Android-latest.apk`, закрытый Basic |
| Legacy Android customer | Отдельный `.github/release/android-customer-stable.json`; публичный `/updates/android/stable.json` и immutable `/releases/android/<code>-<sha>.apk` | `approved:null`, **пустой до приёмки**. Старым клиентам нужен Hostinger bridge |
| Android A1 | BETA16 root HTTPS receipt и timer подтверждены отдельным Android чатом | A1 тестовая линия, НЕ изменять |
| Extension owner | Root утверждает exact GitHub commit+CI run+ZIP SHA из `.github/release/extension-owner-promotions.json`, immutable test ZIP/latest, owner Basic | 0.4.82 и 0.4.83 отозваны, 0.4.84 на проверке; **не восстанавливать автоматически** |
| Extension public | Только Chrome Web Store, Google самостоятельно обновляет установленные расширения | Нет первой карточки Store/идентификаторов/доверенных ключей — **нужен первый ручной выпуск в аккаунте владельца** |

Два runner проверены в CI `45679020658`: ci01 имеет extension+Windows+A1 shared data-only spool, ci02 только extension. Один раз изменить только mounts ci02 после проверки idle; тестовые APK/JVM / Windows CI остаются без SSH/root. Никакие таймеры кроме A1 нельзя объявлять включёнными до root активации.

## Единый защищённый серверный запуск

Однократный root script: `.github/scripts/floki-release-owner-bootstrap.sh`. Получать **только из read-only git mirror** `/home/celikom-mirror/github-mirror.git` по фиксированному full SHA commit и с проверкой Git object blob. Не скачивать shell со случайного HTTPS и не запускать из runner. Нужны один доступ `celops` и заранее подготовленная админская сессия FlokiNET.

При первом запуске:
1. Проверяет существующую подпись Windows 0.24.55, старую точку `stable/current`, root pin, site config, private spool, рабочие команды и зеркальную копию main.
2. Устанавливает и активирует root Windows owner consumer; проверяет именно EXE 0.24.56 через сайт и предыдущий 0.24.55, сохраняет откат.
3. Создаёт отдельный публичный подписанный Windows customer feed, **публикует только уже принятую 0.24.55/seq2** (включая её immutable манифест и EXE, полный HTTP SHA), а 0.24.56 туда не отправляет до явной приёмки. Это нужно для bootstrap, rollback и реального автообновления старых клиентов.
4. Устанавливает root extension owner promoter, не публикует отозванные версии.
5. Устанавливает root legacy Android private signed owner promoter и отдельный отключённый до приёмки публичный OTA.
6. Готовит два отсутствующих data-only mounts ci02, без перезапуска занятого Runner.Worker; при сомнении fail closed.
7. Проверяет статусы таймеров и не изменяет A1/платежи/API/музыку/базу/Hostinger.

После запуска **обязательно** проверить вывод команд, работающие nginx и нужные systemd timers, точный root receipt и authenticated **полный HTTPS GET с SHA** Windows и Android, `ci02` mounts и что Windows public выдаёт только **ранее принятую 0.24.55** (НЕ тестовую 0.24.56), а Android public `approved:null` не раскрывает APK. Дополнительно выполнить один последующий независимый release cycle и тест настоящего обновления с установленной клиентской версии, прежде чем говорить «всё работает». До этого Android public feed пуст, а Windows public feed содержит только уже принятую 0.24.55/seq2. Новые релизы в обоих каналах требуют явной приёмки владельца.

**Не переключать старый Hostinger updater** просто из-за зелёного root таймера: старому Android 0.3.92 нужна отдельная проверка на телефоне и затем атомарное включение на Hostinger ранее подготовленного exact 0.3.94/95 bridge manifest+APK с идентичным старым хостом. Файлы уже лежат в приватном GitHub draft `457921929` и имеют утверждённые SHA. Не передавать signing key и host SSH в untrusted runner.

## Доказательство публикации без повторных заходов по SSH

Одна из задач прежней миграции — разработчик не видел, прошла ли новая версия с CI до сайта. Установщик активирует отдельную root-службу `celikom-release-status.timer`. Она читает **только** завершённые доверенные серверные подтверждения (после полного HTTPS size/SHA), и публикует маленький JSON без версий, приватных URL, capability-токенов, источников или аккаунтов по адресу `https://celikom.com/.well-known/celikom-release-receipt.json`.

Поля `windows_owner_sha256`, `windows_customer_sha256`, `android_owner_sha256`, `android_customer_sha256`, `extension_owner_sha256` равны точному SHA-256 подтверждённой сборки либо `null`, пока её публикация не доказана. Отдельный статус A1 **не выводит** capability URL, проверять существующий подписанный A1 root receipt через его передачу. Timestamp `checked_at` означает обновление статуса, **не** время публикации и не доказывает новую версию сам по себе.

Разработчик сверяет **именно** этот SHA-256 с CI provenance, затем даёт владельцу уже подтверждённую закрытую ссылку на `celikom.com`. У Windows customer после начальной установки SHA будет указывать на ранее принятую 0.24.55, а не на тестовую 0.24.56. Нельзя выводить ссылку по одним лишь GitHub draft/CI log. Если публичный статус не доступен через браузер ChatGPT, использовать точный HTTPS GET из доверенного CI без ключей — но не просить повторно SSH.

## Исправление первой реальной попытки (25.11.2026)

Первый запуск pinned bootstrap `3ab4efd20a92b9fd7035954e135338f6bfbc2da9` завершился непосредственно после `nginx -t`, до первого `CELIKOM_RELEASE_BOOTSTRAP_PRECHECK_OK`. Owner показал read-only диагностикой: Git/Python/Node/systemctl/nginx/apksigner/aapt OK, 38 ГБ свободно, Windows stable `versions/0.24.55`, сайт Nginx читается, файл `/srv/celikom/migration/sites-20261124/android-private/staging-owner-credentials.txt` присутствует, **его UID=1000**. Старый bootstrap ошибочно требовал UID=0. Оригинальный сайт и службы не менять.

Исправлено: bootstrap принимает файл, которым управляет `celops` (проверяет UID, отсутствие symlink, права и формат двух полей), атомарно создаёт **root-only** `/root/celikom-secrets/celikom-owner-basic-verification.txt` с режимом 0600; все три доверенных root-промоутера (Windows/Android/extension) проверяют HTTPS этим локальным root-only файлом. Оригинальному сайту не делать `chown`, `chmod`, не менять его авторизацию. Ошибки теперь отмечаются `CELIKOM_RELEASE_ACTIVATION_STOPPED line=… exit=…` без вывода паролей. При будущей смене пароля Basic необходим безопасный повторный синхронизатор root credentials: повторный bootstrap создаёт копию, но если он уже установлен и требуется ротация вне bootstrap, её надо отдельно выполнять из доверенного root-контекста; не отправлять секрет в чат/CI.

Предыдущий bootstrap с commit `3ab4efd20a92...` **НЕ повторять**. Новые pin SHA и результаты проверок получать из актуальной статической CI после исправления; пока проверка серверной активации не выполнена, не заявлять READY.

## Вторая живая попытка: Windows customer HTTP 403 (25.11.2026)

Вывод первого запуска с исправленными credential checks: preflight PASS, root-only auth snapshot PASS; private Windows owner динамические маршруты nginx -t и анонимный HTTP 401 PASS, root signed 0.24.56 успешно повышена до **закрытой** owner/current, root `celikom-windows-signed-owner.timer` enabled/active. Следующий шаг, публикация **раньше принятой** 0.24.55 в публичный signed customer feed, завершился HTTP 403 на первом запросе `/CELIKOM/Windows/Updates/stable/latest.json`. Installer вывел `CUSTOMER_WINDOWS_FIRST_ACTIVATION_ROLLED_BACK` и общий `CELIKOM_RELEASE_ACTIVATION_STOPPED line=171 exit=1`. Не утверждать, что Windows customer OTA уже работает. Относительно Windows owner предыдущий этап сохранён (откат касался Nginx public route, systemd customer timer и customer consumer, не owner service). Часть файлов customer-stable от первой неудачной публикации может оставаться на диске, но закрытые nginx маршруты восстановления удалены, и это не client release.

Два дефекта выявлены в источниках: customer files были под `/srv/celikom-releases/windows/customer-stable` (родительская private Windows tree может быть недоступна nginx); новая версия `versions/0.24.55` создавалась Python с requested 0755 при `UMask 0077`, реально 0700. Исправлено: только customer feed хранит общедоступные файлы под `/srv/celikom-releases/public/windows-customer-stable` с nginx-traversable dirs; root private signed origins и owner ZIP не открываются. Public location Nginx дополнены `allow all` при `auth_basic off` для исходно закрытого server; добавлена preflight-проверка доступности директорий от `www-data`, и chmod 0755 на **только что созданную публичную директорию конкретной версии**. Аналогично явно allow только public Android OTA и SHA-only receipt, не owner downloads. CI должен подтвердить режим 0755 даже при umask 0077 и все source hash pins. Bootstrap допускает **только точную замену** предыдущего подлинного private intake Windows customer install script, поскольку он остался после отката; произвольную замену не разрешает.

Не запускать прежние pinned bootstrap `f2fdb044b01b8926b201ab6650e7185e50f86236`; использовать новую схему по финальной зелёной CI. После server retry тестировать HTTP 200 + complete SHA для 0.24.55 и 401 для private owner 0.24.56, затем остальные каналы. Публичная 0.24.56 остаётся **непринятой**.

## Как выпускать новые версии после однократного запуска

**Windows:** следующий подписанный private candidate через привычный workflow на `main`. Root independently verifies и сам обновляет *закрытый тестовый* owner latest; разработчик даёт только `https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe` после real HTTPS verification. Владелец вручную устанавливает в единственную CELIKOM. После «принимаю X» обновить только `.github/release/windows-customer-stable.json` с *точным* номером/sequence/SHA и `owner_accepted:true`. Отдельный root timer проверяет P-256/immutable installer/full HTTPS и обновляет публичный latest и подписанный feed. Не заменять тестовый APK/EXE другим содержимым под тем же номером.

**Legacy Android:** подписанный приватный candidate через `.github/release/android-stable-owner-request.json` + `android-stable-owner-floki-spool.yml`; сайт owner latest после root signer validation. Публичный `.github/release/android-customer-stable.json` с exact code/name/SHA/`owner_accepted:true` только после приёмки. Первая миграция Android 0.3.92 через Hostinger — отдельный обязательный этап. Никаких public A1 релизов.

**Extension:** ZIP при изменении extension в `main` проходит Floki CI. В `.github/release/extension-owner-promotions.json` добавляется exact source/run/ZIP sha только для проверяемого кандидата; timer обновляет **только закрытый** owner latest. Отозванные 0.4.82/83 не публиковать. Для клиентов нужна **Chrome Web Store** карточка, первая загрузка и listing/privacy вручную владельцем; затем разрешён API V2 upload + publish с сервисным аккаунтом. Никогда не обещать автообновление ZIP, распакованного вручную.

## Сайт и кнопка скачивания

Действующий сайт CELIKOM всё ещё сохраняет ранее согласованный **закрытый статус установки** в CMS (Stage 8 текст «Идёт тестирование», «Пока установка закрыта»). Серверная настройка не должна самовольно превращать этот текст в «Скачать» или переписывать дизайн. Подготовлен постоянный public Windows URL `https://celikom.com/downloads/windows/CELIKOM-Windows-stable.exe`; при первом серверном запуске он отдаёт **только ранее принятую 0.24.55**. При разрешении начать публичные продажи надо отдельно перевести **одобренную CMS-редакцию** из closed-installation в реальную установку и привязать кнопку Windows к этому постоянному URL; для Chrome/Brave использовать только настоящий Chrome Web Store listing URL после создания карточки, для Android — настоящий принятый `/releases/android/...` или безопасный указатель. Не обещать, что кнопка текущего сайта уже автоматически переключена: это предстоит проверить и утвердить в административной сессии.

## Acceptance checklist

- [ ] Один защищённый запуск root script, все таймеры active и site Nginx -t, ни одна ранее рабочая служба не ухудшилась.
- [ ] Windows 56 owner complete GET SHA match, Windows customer default `approved:null`, HTTPS signed baseline 0.24.55 GET+SHA и отсутствие публичной тестовой 0.24.56.
- [ ] Android 95 owner root certificate/manifest/download proof, Android customer default `approved:null`, BETA16 сохранён.
- [ ] Оба runner видят только нужные private data-only каталоги; самостоятельные последующие сборки проходят по обоим исполнителям.
- [ ] Owner отклоняет неудачную версию без публикации для клиентов, принимает следующую exact версию.
- [ ] Реальное Windows auto update old→accepted new (тихая установка, перезапуск, rollback).
- [ ] Реальное Android old Hostinger→0.3.94 с тем же сертификатом и затем celikom.com OTA.
- [ ] Chrome Web Store listing и verified store update; сайт ссылается на **реальную** карточку (не выдуманный URL).
- [ ] Только после этого можно выводить Hostinger из эксплуатации.

