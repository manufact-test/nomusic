# CELIKOM — утверждённая инфраструктурная схема и контрольные точки (22.11.2026)

**Последняя контрольная точка 23.11.2026 и инструкция следующему чату:** [CELIKOM-NEXT-CHAT-START-2026-11-23.md](CELIKOM-NEXT-CHAT-START-2026-11-23.md). При расхождении сведений приоритет у нового документа.

## Обязательные решения владельца
- **GitHub `manufact-test/nomusic` остаётся основным ПРИВАТНЫМ репозиторием**. Разработка через обычный чат ChatGPT с GitHub-коннектором должна продолжаться без изменения привычных действий владельца.
- **Forgejo на FlokiNET используется как независимое резервное зеркало GitHub (односторонне GitHub → Forgejo)**. Не допускать двухсторонней записи и переписывания веток; синхронизация настроена через systemd timer 15 минут (нужно подтвердить самостоятельный запуск таймера).
- **FlokiNET Romania VPS** — целевая площадка API, библиотеки треков и сборочной инфраструктуры. Не увеличивать ежемесячные расходы. Self-hosted runners или Forgejo Actions использовать только с проверенной изоляцией и лимитами; production-секреты, БД и музыкальные файлы должны оставаться недоступными сборкам.
- **Сначала** полный переезд и тестирование работоспособности CELIKOM, затем проверка сборки/разработки всех **трёх** вариантов (Windows, расширение браузера, Android) из обычного чата, затем отключение старых ресурсов; **онлайн-платежи подключаются позже**. Дедлайн запуска оплаты перенесён, спешка отменена.
- НЕ отключать GitHub до подтверждения функционирования разработки; НЕ выключать Hostinger до проверки всех реальных зависимостей и обновлений. Никаких дополнительных платных подписок без согласования.
- Не менять существующую архитектуру приложений без необходимости. Не вынуждать владельца пользоваться IDE, PowerShell, ADB, или вторым телефоном. Установка и диагностика с его стороны должны быть минимальными.

## Состояние на 22.11.2026
- VPS: Ubuntu 24.04, x86_64, 4 vCPU, 3.8 GiB RAM, ~87 GiB disk (73 GiB свободно до swap), Docker, Nginx, PHP 8.3, MariaDB Docker, Forgejo.
- Проверка Docker sandbox 22.11.2026 успешна: Alpine 3.21 под UID/GID `997:988`, лимит CPU 1.5, RAM 1800M, RAM+swap 3300M, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, `--read-only`, без mounts или docker.sock; GitHub API доступен; результат `PRODUCTION_PATHS_HIDDEN`, `GITHUB_NETWORK_OK`, `CELIKOM_CI_SANDBOX_OK`. **Это только предварительный smoke-test; доступ к сети хоста/сервисам и безопасность исполнения workflow не доказаны. Runner ещё не зарегистрирован.**
- `celikom-ci`: пользователь создан (shell nologin). `celikom-ci.slice` с CPU 150%, MemoryHigh 1200M, MemoryMax 1800M, MemorySwapMax 1536M, TasksMax 200 создан; **runner ещё не установлен / не запущен, slice ещё не привязан к его службе**. Swap 4.0 GiB создан (`/swapfile-celikom`, swappiness 10).
- Forgejo `celadmin/nomusic` приватный, импорт GitHub: 1421 ветка, 3238 коммитов, 19 issues и 16 PR. `main` в Forgejo и `source-main` совпадали по `4538934e` на момент проверки. Зеркало и systemd timer настроены, 1421/1421 веток сверены по SHA; подтверждение самостоятельного запуска timer ещё впереди.
- HTTPS `api.celikom.com` установлен, цепочка TLS проверена, Certbot dry run успешен, deploy hook делает `nginx -t` и reload; публичный API пока закрыт и отвечает 404 — **продакшен не включён**.
- Hostinger копия музыки ~9.1 GiB и БД 44 таблицы перенесены на VPS. Проведены проверки целостности музыкальных файлов и тесты API/auth в изолированном staging.
- Внешний резерв CELIKOM: зашифрованный GPG AES256 архив ~9.1 GiB и отдельный ключ перенесены на Windows, SHA256 архива совпал с серверным: `9d94a07d3306acd8874a7d3ad959234427d67a0d1b9c402526abb492e3acff15`. Хранить ключ отдельно; финальный дельта-бэкап и восстановительный тест ещё нужны.
- Почта: исходящие SMTP 465/587 с FlokiNET не работают, открыт тикет **#477936**. Нельзя считать регистрацию готовой до проверки реальной доставки.
- Оплата: в приложении есть `BillingAdapter` интерфейс, `WebhookService`, `SubscriptionService`, но **нет concrete BillingAdapter / checkout wiring / платёжных конфигураций**. Ноль реальных платежей и подписок на момент аудита. По решению владельца это после миграции.
- Windows `windows-companion/w15/Celikom.Companion/MainWindow.cs` содержит `DefaultApiOrigin` со старым `darkred-camel-588676.hostingersite.com`.
- Android активная ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`: `ApiContract.java` также содержит Hostinger URL; `UpdateCenter.java` использует `lemonchiffon-narwhal-791953.hostingersite.com` как адрес обновлений. Этот второй Hostinger **нельзя удалять без проверки**, а некоторые workflow получают с него исходный APK и используют временные GitHub artifacts.
- Статистическая инвентаризация `runs-on`: main 96 `ubuntu-latest`, 72 `windows-2022`, 27 `ubuntu-22.04`, 4 `ubuntu-24.04`, 3 `windows-latest`, 1 ARM; Android ветка 90 `ubuntu-latest`, 52 `ubuntu-24.04-arm`, 37 `ubuntu-24.04`, 3 macOS, 1 matrix. Это упоминания, а НЕ число выполненных jobs.
- Нельзя объявлять один x86_64 VPS полной заменой Windows/macOS/ARM runner: требуется отдельный план для каждого типа сборки. Цель — не расходовать бесплатные квоты и платные минуты GitHub, сохранив нынешнюю доступность готовых APK/EXE/расширения и стабильные ссылки.

- Официальный контейнер GitHub Actions runner `ghcr.io/actions/actions-runner:2.338.2` скачан и в `--network=none` проверен без регистрации: UID/GID `1001:1001`, `config.sh` и `run.sh` исполняемы, результат `CELIKOM_OFFICIAL_RUNNER_READY`. **Runner пока не зарегистрирован и задания не принимает.**
- Согласно документации Forgejo 17, существующий нормальный репозиторий НЕ может быть превращён в встроенный pull mirror без повторного создания; текущий `celadmin/nomusic` с 19 issues и 16 PR сохраняем, не удаляем ради зеркала. Потребуется другой односторонний sync (приватный GitHub read-only источник + безопасное обновление refs через штатный git transport), с контрольными проверками.

- GitHub Deploy Key `celikom-floki-github-readonly` добавлен владельцем для `manufact-test/nomusic` без записи. Тест с VPS пользователем `celikom-mirror`: `git ls-remote git@github.com:manufact-test/nomusic.git refs/heads/main` вернул `248c643e...`, `CELIKOM_GITHUB_READ_OK`. Доступ GitHub → FlokiNET подтверждён.
- Forgejo SSH конфигурация: `SSH_DOMAIN=127.0.0.1`, `SSH_PORT=22`, `DISABLE_SSH=false`; Forgejo HTTP слушает `127.0.0.1:3000`, OpenSSH на порту 22. Штатный Git push идёт на `git@127.0.0.1` с отдельным Forgejo deploy key записи только в `celadmin/nomusic`. **Ключ и sync настроены, периодический tick отдельно проверить**; прямую модификацию bare Git каталога Forgejo не использовать.

- 23.11.2026: GitHub→Forgejo: `main` успешно pushed, затем 1421 ветка успешно массово передана через `git push --atomic` (без force, без delete). Сравнение нормализованных `SHA ref` локального зеркала и `git ls-remote --heads forgejo`: 1421/1421 совпадают, результат `CELIKOM_ALL_1421_BRANCHES_VERIFIED`. Тегов в источнике 0. **Периодическая синхронизация настроена 23.11.2026, самостоятельный tick нужно подтвердить.**

- 23.11.2026: на VPS создан `/usr/local/sbin/celikom-mirror-sync` (запуск от `celikom-mirror`, GitHub read key → Forgejo write key, `flock`, без force push/удаления), ручной запуск дал `VERIFIED_REFS=1421` и `CELIKOM_MIRROR_SYNC_OK`. Созданы `celikom-mirror-sync.service` с hardening/CPU/Memory ограничениями и `celikom-mirror-sync.timer` каждые 15 минут; после стартовой проверки `Result=success`, `ExecMainStatus=0`, таймер включён, `CELIKOM_MIRROR_TIMER_CONFIGURED`. Следующий контроль: убедиться, что самостоятельный запуск по таймеру доходит до `CELIKOM_MIRROR_SYNC_OK` и переносит свежий коммит документации без ручного запуска.

- 23.11.2026: CI security audit: одноразовый Docker Alpine контейнер в стандартной сети `bridge` достучался до SSH хоста через gateway (`CI_CAN_REACH_HOST_SSH`). UFW active, разрешены 22/80/443 (включая IPv6), `DOCKER-USER` пока без правил, Docker networks на момент первого аудита были bridge/host/none, затем создана отдельная `celikom-ci-net` с интерфейсом `br-celikomci`. **Self-hosted runner не зарегистрирован; соединение Docker→host нужно закрыть через отдельную CI-сеть и проверенные firewall rules прежде чем пускать workflow.**
- Timer `celikom-mirror-sync.timer` enabled+active; журнал `celikom-mirror-sync.service` показывал успешный запуск в 23:18:42–23:18:48 с `VERIFIED_REFS=1421`, но это мог быть первоначальный ручной `systemctl start`: самостоятельный scheduled tick ещё не подтверждён на момент аудита.

- 23.11.2026: временное правило `iptables -I INPUT -i br-celikomci -j REJECT` проверено: `CI_HOST_SSH_BLOCKED`, `CI_GITHUB_INTERNET_OK`, `CELIKOM_CI_NETWORK_TEST_OK`. После теста trap удалил правило. **Защита НЕ постоянная**, runner по-прежнему НЕ зарегистрирован. Дальше создать узкие постоянные ограничения и проверить доступ к прочим сервисам VPS/Docker, не затронув production.

## Очередность дальнейших действий
1. Прежде чем активировать self-hosted runner, проверить права доступа к секретам и изоляцию. Self-hosted workflows могут исполнять произвольный код; пользователь `celikom-ci` и cgroup сами по себе не являются достаточной защитой. Рассмотреть одноразовую ограниченную контейнерную среду без Docker socket, host mounts, root, и доступа к production network.
2. Настроить одностороннее приватное GitHub → Forgejo зеркало и контролировать совпадение refs; не смешивать CI и backup-секреты.
3. Подключить **только явно разрешённые тестовые** CI jobs к self-hosted runner. Проверить, что они не используют GitHub-hosted Actions minutes, что артефакты и подписи корректны. Не менять все `runs-on` разом.
4. Аудит URL, ключей подписи, артефактов, auto-updates и секретов всех трёх клиентов. Подготовить перенос Android base APK из Hostinger и постоянных URL обновлений.
5. Завершить SMTP тикет #477936, сделать реальный тест письма; восстановительный тест backup и финальная дельта-синхронизация БД и медиа; переключить API на `api.celikom.com` без регрессий.
6. После подтверждения реально работающих Windows, browser extension и Android сборок через ChatGPT, и сервера/пользователей на FlokiNET, отключить Hostinger и ненужные ресурсы.
7. После всего отдельно заняться платёжным провайдером, подписками и приёмкой real checkout/webhook/refund.

Не включать платёжные флаги, не удалять старую инфраструктуру и не объявлять миграцию завершённой до проверок.
