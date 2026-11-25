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
| Windows customer | Отдельная подпись+SHA проверка из доверенного immutable owner-store, `.github/release/windows-customer-stable.json`, динамический публичный `/downloads/windows/CELIKOM-Windows-stable.exe` и `/CELIKOM/Windows/Updates/stable/latest.json[.sig]` | `approved:null`, канал пуст до разрешения; old→new ещё не принят |
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
3. Создаёт **пустой** публичный подписанный Windows consumer feed, отдельный от тестового latest.
4. Устанавливает root extension owner promoter, не публикует отозванные версии.
5. Устанавливает root legacy Android private signed owner promoter и отдельный отключённый до приёмки публичный OTA.
6. Готовит два отсутствующих data-only mounts ci02, без перезапуска занятого Runner.Worker; при сомнении fail closed.
7. Проверяет статусы таймеров и не изменяет A1/платежи/API/музыку/базу/Hostinger.

После запуска **обязательно** проверить вывод команд, работающие nginx и нужные systemd timers, точный root receipt и authenticated **полный HTTPS GET с SHA** Windows и Android, `ci02` mounts и что публичные `approved:null` **не раскрывают** APK/EXE. Дополнительно выполнить один последующий независимый release cycle и тест настоящего обновления с установленной клиентской версии, прежде чем говорить «всё работает». До этого Windows/Android public feed пусты, это не баг, а защита.

**Не переключать старый Hostinger updater** просто из-за зелёного root таймера: старому Android 0.3.92 нужна отдельная проверка на телефоне и затем атомарное включение на Hostinger ранее подготовленного exact 0.3.94/95 bridge manifest+APK с идентичным старым хостом. Файлы уже лежат в приватном GitHub draft `457921929` и имеют утверждённые SHA. Не передавать signing key и host SSH в untrusted runner.

## Как выпускать новые версии после однократного запуска

**Windows:** следующий подписанный private candidate через привычный workflow на `main`. Root independently verifies и сам обновляет *закрытый тестовый* owner latest; разработчик даёт только `https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe` после real HTTPS verification. Владелец вручную устанавливает в единственную CELIKOM. После «принимаю X» обновить только `.github/release/windows-customer-stable.json` с *точным* номером/sequence/SHA и `owner_accepted:true`. Отдельный root timer проверяет P-256/immutable installer/full HTTPS и обновляет публичный latest и подписанный feed. Не заменять тестовый APK/EXE другим содержимым под тем же номером.

**Legacy Android:** подписанный приватный candidate через `.github/release/android-stable-owner-request.json` + `android-stable-owner-floki-spool.yml`; сайт owner latest после root signer validation. Публичный `.github/release/android-customer-stable.json` с exact code/name/SHA/`owner_accepted:true` только после приёмки. Первая миграция Android 0.3.92 через Hostinger — отдельный обязательный этап. Никаких public A1 релизов.

**Extension:** ZIP при изменении extension в `main` проходит Floki CI. В `.github/release/extension-owner-promotions.json` добавляется exact source/run/ZIP sha только для проверяемого кандидата; timer обновляет **только закрытый** owner latest. Отозванные 0.4.82/83 не публиковать. Для клиентов нужна **Chrome Web Store** карточка, первая загрузка и listing/privacy вручную владельцем; затем разрешён API V2 upload + publish с сервисным аккаунтом. Никогда не обещать автообновление ZIP, распакованного вручную.

## Acceptance checklist

- [ ] Один защищённый запуск root script, все таймеры active и site Nginx -t, ни одна ранее рабочая служба не ухудшилась.
- [ ] Windows 56 owner complete GET SHA match, Windows customer default `approved:null` и no public unexpected download.
- [ ] Android 95 owner root certificate/manifest/download proof, Android customer default `approved:null`, BETA16 сохранён.
- [ ] Оба runner видят только нужные private data-only каталоги; самостоятельные последующие сборки проходят по обоим исполнителям.
- [ ] Owner отклоняет неудачную версию без публикации для клиентов, принимает следующую exact версию.
- [ ] Реальное Windows auto update old→accepted new (тихая установка, перезапуск, rollback).
- [ ] Реальное Android old Hostinger→0.3.94 с тем же сертификатом и затем celikom.com OTA.
- [ ] Chrome Web Store listing и verified store update; сайт ссылается на **реальную** карточку (не выдуманный URL).
- [ ] Только после этого можно выводить Hostinger из эксплуатации.

