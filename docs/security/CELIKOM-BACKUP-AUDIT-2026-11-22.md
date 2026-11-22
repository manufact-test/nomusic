# CELIKOM — аудит резервирования перед миграцией

**Дата:** 2026-11-22. **Статус:** подтверждены резервные копии Git и CMS, SQL snapshot/restore основного сервера и хеш-аудит аудио. **НЕ завершено** независимое offsite-копирование основного SQL и самих аудиофайлов, а также ключей подписи и релизных артефактов. Ни один production-объект не изменён.

Основания: `docs/security/CELIKOM-PRIVACY-AND-SECURITY-PLAN.md`, `docs/adr/0002-public-development-private-release.md`, `docs/runbooks/stage14-hardening.md`, `docs/deployment/hostinger-stage5-operations.md`, `docs/website/checkpoints/2026-10-18-V5-18-FINAL-STAGING-CLOSEOUT.md`, `docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md`, Android handoff.


## Исполнение 22.11.2026 — проверено по реальным Actions

Этот раздел имеет приоритет над первоначальным аудитом ниже, который фиксировал состояние **до** выполнения резервирования.

| Объект | Результат | Доказательство |
|---|---|---|
| Git full mirror | **PASS**: все **1 421** ветки, 0 tags; bundle создан и проверен восстановлением списка refs; зашифрован возрастным ключом age на отдельный SSH recipient | Workflow [45041712215](https://github.com/manufact-test/nomusic/actions/runs/45041712215) |
| Git ciphertext | **PASS**: приватный каталог Hostinger `celikom/backups/git-mirror/celikom-git-full-45041712215.age`, SHA-256 `33815437d2938b76d94048b64a1926d832b7213bde8407f546cba2b6640db1ad` | Remote checksum compared byte-for-byte; **no** GitHub artifacts |
| Backend snapshot | **PASS**: свежий приватный SQL-дамп **43 таблиц**, копия закрытой конфигурации, SHA-256 inventory **1 545** аудиофайлов; аудиофайлы **не скопированы** | Workflow [45041366103](https://github.com/manufact-test/nomusic/actions/runs/45041366103) |
| Restore backend | **PASS**: изолированное восстановление SQL **43 таблиц** и сверка количества строк, hash-check всех 1 545 исходных аудио, конфигурация; live БД не менялась | Workflow [45041783963](https://github.com/manufact-test/nomusic/actions/runs/45041783963) |
| Default restricted request | **PASS**: `.github/deploy/hostinger-stage5-request.json` возвращён в режим `audit`; последующая проверка SUCCESS | Workflow [45042303667](https://github.com/manufact-test/nomusic/actions/runs/45042303667) |
| Website/CMS | **PASS**: отдельный зашифрованный архив приватных и публичных файлов сайта плюс SQL **11 таблиц**; дамп импортирован в disposable MySQL, публикации существуют | Workflow [45042927595](https://github.com/manufact-test/nomusic/actions/runs/45042927595), финальная повторная проверка [45043191558](https://github.com/manufact-test/nomusic/actions/runs/45043191558) |
| Website ciphertext | **PASS**: приватный каталог Hostinger `celikom-private/backups/precutover/website-cms-45043191558.age`, SHA-256 `9bc1546e7274c86dbced3d012b01ed8a826ee30ba58e00ded8d77847218a3757` | Encrypted remote SHA verified |
| CI после исправления PHP newline | General CI **PASS** on `44d3917bcf16e9f4b75719e8ed44c8f2d85adfa0`; Windows integration **PASS** on same code checkpoint ([45043191610](https://github.com/manufact-test/nomusic/actions/runs/45043191610)) | Workflow [45043191590](https://github.com/manufact-test/nomusic/actions/runs/45043191590) |

**Recovery identity:** archives use the same *public* SSH Ed25519 recipient (`ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINWjfyJq4jT+q78CczF7TQM1R2HgjLWjJmfJwafEe9bx`). The corresponding private recovery key was generated outside GitHub and Hostinger and linked to the owner in ChatGPT; **owner's secure offline custody is not yet confirmed**. Never put the private key, users' SQL, unencrypted media or env into repository or workflow artifacts. To restore encrypted backups use `age -d -i <owner-key> archive.age` in a trusted offline environment, check SHA-256 of ciphertext first, and test `git clone --mirror` or isolated MySQL before cutover.

**Still P0 / NO-GO for provider-loss recovery:** the full original **1 545 audio files** have **not** been transferred off Hostinger; SQL snapshot and site backup ciphertext are **also on Hostinger**, not yet in independent offsite storage. No FlokiNET IP/credentials or verified SSH access has been provided. Source GitHub release assets/PR metadata and private app signing keys still require separately verified custody. Do not shut down Hostinger or start paid subscriptions based on these backups alone.

**Immediate next action:** obtain one secure FlokiNET initial-access channel (owner's hosting panel/SSH bootstrap) and stream verified encrypted media + current databases + website/Git archives to the new VPS, then a second independent backup destination. Keep minimal owner involvement and current ChatGPT Plus / GitHub Private / self-hosted-runner strategy. Do not alter application architecture or branch history.

---

## 1. Проверено по GitHub 22.11.2026

- Репозиторий `manufact-test/nomusic`: **Private**, ChatGPT-коннектор сохранил чтение и запись.
- Основная ветка `main`: `1f4272f2b1e22569644b32b381ed6f95b872c7d2` **на момент аудита**. Windows — принятая владельцем линия 0.24.54.0. Ветка `backup/windows-main-pre-w173-consolidation-20261121` существует и указывает на `affb7b225d2e7eb2835f53294e975a1e60bb758b`; это точка восстановления в рамках GitHub, **не независимый backup**.
- Android A1: `experiment/android-a1-metrica-init-state-observer-arm13-20261112` @ `c17c473c8ac000f205aec0effa980e8ac72ea18e` на момент аудита. Последняя документированная BETA12 **не имеет подтверждённой реальной подмены на телефоне**. BETA12 export workflow `44898991151` — SUCCESS 21.11.2026, но это не проверка восстановления APK. Артефакт в handoff обозначен как истекающий **28.11.2026** — архивировать отдельно до истечения.
- Получен список `refs/heads`: **1 421 ветка**, из них **1 157** в `backup/*`. Очистку и force-push до создания проверенного Git mirror **запрещаем**; не ограничиваться `main`/Android.
- В репозитории обнаружены **3 draft releases**. Git tags, Git LFS, все release assets, Actions artifacts, Issues/PR metadata и Packages **пока не инвентаризированы как восстановимые**. Git mirror сам по себе не переносит все эти сущности.
- Ранее опубликованные коммиты/артефакты могли быть скопированы третьими лицами; переход в Private не может отозвать существующие копии.

## 2. Что подтверждено по старым восстановительным проверкам

- `37903842547` — 09.10.2026, **SUCCESS**: Stage 5 private snapshot, согласно runbook включал приватную конфигурацию, аудио и SQL таблицы тестового этапа.
- `37903962631` — 09.10.2026, **SUCCESS**: restore-drill файлов и SQL в изолированную MySQL, без записи в live БД.
- Это **исторические** результаты: ни текущую полноту данных, ни новую копию от 22.11.2026, ни восстановление всей современной схемы они не подтверждают. В исходном описании Stage 5 речь шла о **6 таблицах**, а база продукта расширялась после октября.
- `.github/deploy/hostinger-stage5-request.json` на `main` содержит `{"operation":"audit"}`. Это запрос на аудит, **не факт создания свежего snapshot**. Новый workflow не запускался.
- Старый runbook явно признаёт, что постоянные бэкапы находятся **на том же Hostinger**, что и production; независимый зашифрованный offsite backup и восстановление при утрате провайдера не доказаны.
- Сайт и временная CMS исторически размещались отдельно от API, с **отдельной MySQL**, пользовательским контентом и медиа. Их нужно копировать **самостоятельно**, даже если основная БД/API успешно восстановятся.
- Подписи Android, Windows-манифестов и существующая схема автообновлений требуют сохранения текущих signing identities/ключей. Наличие и возможность восстановления **действительных** приватных ключей данным аудитом не подтверждены. Никогда не помещать их в Git, общие CI-артефакты или чат.

## 3. Матрица состояния

| Объект | Что уже есть | Что отсутствует / пока не доказано |
|---|---|---|
| Git-история | Private GitHub, refs, Windows backup branch | Зашифрованный независимый mirror всех refs/tags/objects с проверкой restore |
| GitHub metadata | 3 draft releases, известные workflow и handoff | Полный каталог release assets, PR/Issues, LFS/Packages, нужных артефактов |
| Backend DB | Исторический Stage5 snapshot+restore | **Свежий консистентный дамп полной production-БД**, схемы и ledger |
| Аудиотека | Историческая проверка приватных файлов и SHA-256 | **Свежая полная копия**, актуальные связи catalog/storage и hash manifest |
| Сайт/CMS | Документировано независимое тестовое хранилище и MySQL | Свежая копия **отдельной** БД, медиа и публикаций |
| Конфигурация | Приватные env и restricted scripts описаны | Зашифрованная копия live env/конфигурации, перечень secret names, восстановление |
| Ключи и подписи | Планы Android/Windows signing и release gates | Защищённая копия **реальных** приватных ключей и offline recovery check |
| Приложения/релизы | Windows owner accepted 0.24.54.0; Android BETA12 artifact | Архив точных проверенных APK/installer/extension ZIP и SHA256 вне истекающих Actions |
| Провайдер и offsite | Исторический Hostinger snapshot | Не менее **одной проверенной зашифрованной копии вне Hostinger и FlokiNET** |
| Доступ/откат | Иммутабельные старые backend releases, Git refs | Полный тест rollback нового VPS без перезаписи изменённой live БД |

## 4. Обязательная последовательность ДО переноса production

1. **Git mirror/export:** из доверенного окружения сделать полный `git clone --mirror` (включая все refs), проверить число ссылок и наличие объектов, отдельно выгрузить нужные release assets, metadata, при наличии LFS. Зашифровать локально до отправки во внешнее хранилище, зафиксировать SHA-256 и сделать тест чтения. Не сохранять открытый архив в публичных GitHub artifacts.
2. **Hostinger snapshot:** через существующую ограниченную процедуру или эквивалент с доверенным доступом создать **свежие** consistent backups всех актуальных production БД и файлов (не только исторические 6 таблиц), включая media и каталог, конфигурации и migrations. Никакого live restore, удаления или изменения музыкальных статусов.
3. **Website/CMS snapshot:** отдельно снять БД, медиатеку и текущие публикации/черновики, проверить владельческие изменения.
4. **Секреты и ключи:** безопасно определить место хранения и наличие текущих signing/release/SSH/API/payment ключей. Сделать закрытые зашифрованные recovery copies; не печатать значения и не генерировать новые подписи вместо существующих без решения владельца.
5. **Независимый offsite:** хотя бы одна копия вне **обоих** провайдеров. Если бесплатного/имеющегося пространства не хватает — **остановить переключение**, предложить экономный вариант, не покупать без согласия.
6. **Restore drill:** на изолированном окружении импортировать оба дампа, проверить таблицы, основные учётные записи (без раскрытия PII), media hashes, разрешённый mapping, signed audio/Range, CMS publish, rollback файлов. Зафиксировать проверенный recovery point.
7. **Только после** backup+restore gate — FlokiNET setup/cutover, синхронизация изменений БД перед DNS, проверка клиентов. Hostinger держать неизменённым резервом до приёмки.

## 5. Ограничения текущего этапа и следующая задача

- В обычном чате сейчас доступен GitHub-коннектор. **Непосредственный SSH/SFTP к Hostinger/FlokiNET и безопасное offsite хранилище не подключены**: я не могу подтвердить наличие или создать живой SQL/audio backup одним чтением документации.
- Текущее действие — **инвентаризация**, никакие production данные/секреты не скачаны, не изменены, не скопированы.
- Следующий шаг: организовать закрытый способ создания и получения шифрованного Git mirror и свежего Hostinger snapshot (без открытых файлов в GitHub Actions); проверить объёмы для 90 GB FlokiNET и доступного независимого хранилища. Не устанавливать runner в production-контур до изоляции и резервного копирования.
- Коммерческий релиз по-прежнему **NO-GO** до проверенных P0 backup, безопасности, оплаты и прав на контент. Срочность не является доказательством готовности.

**Owner rules:** ChatGPT Plus/обычные чаты, без новых подписок, минимум участия владельца, все линии разработки продолжаются, никакой очистки веток и изменений архитектуры.
