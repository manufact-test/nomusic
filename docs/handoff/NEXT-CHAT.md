# CELIKOM — актуальная передача в новый чат

Дата сверки: **2026-10-09**. Этот файл — краткое текущее состояние, а не новое продуктовое ТЗ. Архивные прежние сообщения handoff не использовать в качестве очередного действия.

## Авторитетные файлы и порядок

- **CELIKOM Master ТЗ MVP v1.5 (09.10.2026)** — основная спецификация, сохранена в Library /CELIKOM как CELIKOM_Master_TZ_MVP_v1.5_2026-10-09.docx (libfile_af7d67f2cc848191947f897a5606675c).
- **CELIKOM План работ MVP v1.6 (09.10.2026)** — последовательный roadmap 0–18, сохранён в Library /CELIKOM как CELIKOM_Plan_Rabot_MVP_v1.6_2026-10-09.docx (libfile_4841b3eb31f0819186f49ff9c42cfe4b).
- Развёрнутая передача: CELIKOM_HANDOFF_STAGE6_2026-10-09.md в Library /CELIKOM (libfile_9e57df9dff68819190bc0836ba16ee5a).
- Выполнение: ../project-status.md; операции: ../deployment/hostinger-stage5-operations.md; протокол: ../test-plans/CELIKOM-STAGE5-LIVE-AUDIO.md. Если план расходится с Master ТЗ, приоритет за Master ТЗ.

## Реальное состояние на 09.10.2026

- **Этапы 0–5 приняты в рамках owner-only private testing. Этап 6 — следующий, пока НЕ реализован.**
- Extension **0.4.4**, активный Hostinger release **0.4.4-0fee5892c82d01e8fe7936d76f064c48484f136d**, независимый серверный API version **0.4.0**.
- API origin https://darkred-camel-588676.hostingersite.com. FEATURE_REPLACEMENTS=1, FEATURE_ANALYTICS=0. Данные и .env в приватном celikom/shared (audio, staging); backups/stage5 вне public_html.
- Первый одобренный владелецем MP3: Яндекс Track ID **144530503**, Replacement ID **1**, duration **180872 ms**. Расширение реально воспроизводит его через подписанные HTTP Range, MediaSource/blob и применяет fail-open.
- Владелец подтвердил **6/6 функциональных** + **6/6 стабильностных** сценариев на 0.4.4. CSP Яндекс Музыки блокирует прямой host audio.src; нельзя регрессировать к прямому src. В 0.4.4 исправлено аварийное отключение с возвратом оригинала.
- Не блокирующее UX-ограничение: после отключения и повторного включения расширения в chrome://extensions надо единожды обновить уже открытую вкладку Яндекс Музыки.
- Приватный snapshot .env/audio/SQL создан; файлы восстановлены в отдельный каталог, SQL — в disposable MySQL, рабочие данные не менялись. При повторном deploy SHA-256 .env/audio и counts 6 таблиц совпали; подписанный MP3 и Range проверены. Внешний 6-часовой мониторинг API активен.
- Это **не production readiness**: backup остаётся на Hostinger (нет независимого offsite), намеренный live outage и rollback не проводились; пользовательских uploads/админ-модерации, аккаунтов, trial, подписок, рефералов, Android playback ещё нет.

## GitHub / deployment

Repo https://github.com/manufact-test/nomusic
Ветка feature/api-range. **PR #6 открыт к develop, НЕ СЛИТ**, не сливать без прямого разрешения владельца. Проверять актуальный branch HEAD перед изменениями. Не трогать другие сайты Hostinger.
CI 0.4.4: https://github.com/manufact-test/nomusic/actions/runs/37900547793 (70 tests).
Repeat deploy: https://github.com/manufact-test/nomusic/actions/runs/37904158336.
Snapshot: https://github.com/manufact-test/nomusic/actions/runs/37903842547.
Restore: https://github.com/manufact-test/nomusic/actions/runs/37903962631.
Post-deploy integrity: https://github.com/manufact-test/nomusic/actions/runs/37904416817.
Signed audio: https://github.com/manufact-test/nomusic/actions/runs/37904551511.

Existing repository Actions secrets HOSTINGER_SSH_KEY, HOSTINGER_DB_PASSWORD are configured; do not request/reset/show them. Never expose beta token, signing key, private MP3, SQL dumps or signed URLs. PHP CLI 8.3 uses /opt/alt/php83/usr/bin/php. Use GitHub Actions for remote work; direct container SSH was previously restricted.

## Exactly next: Stage 6 shared replacements library

1. Read BOTH DOCX master files, then inspect GitHub branch implementation, migrations, PdoCatalogRepository / ResolveService / LocalStorageAdapter, APIs, cache and current CLI. Show a concrete matrix of existing vs missing functionality. **Do not immediately write duplicative code.**
2. Plan and implement safe internal library seed/management CLI and Track — AudioAsset — TrackReplacement relations. One audio object can link to multiple exact Track IDs; only one approved active replacement per Track.
3. Validate server-driven switching without extension rebuild; positive/negative cache TTL, negative cache freshness after approve, absence of repeated resolve every second, fail-open for unmapped IDs.
4. Cover two independent installations getting one approved replacement; two IDs sharing one physical AudioAsset; unknown Track original; cache and privacy regression.
5. Run tests/CI and owner-only end-to-end gate. No client-facing upload/publishing before manual moderation stages. Only then mark Stage 6 accepted.

Work maximally autonomously through GitHub/Actions and ask the owner for Chrome actions only at real browser acceptance. Do not repeat server access setup, token retrieval, uploading first song or Stage 5 owner tests.

## First-message template

Продолжаем CELIKOM с этапа 6 — общая библиотека replacements. Авторитетные документы: CELIKOM Master ТЗ MVP v1.5 и План работ MVP v1.6 (09.10.2026). GitHub manufact-test/nomusic, branch feature/api-range, PR #6 открыт, не сливать. Этап 5 owner-only принят: extension 0.4.4 воспроизводит реальный MP3 через Hostinger, 6/6 + 6/6 живых тестов; repeat-deploy, приватный snapshot, отдельное восстановление SQL и мониторинг проверены. Не повторяй тесты и настройку. Сначала изучи документы, проверь актуальный код и дай точную матрицу уже реализованного и технический план Stage 6. Работай самостоятельно через GitHub Actions, сохраняй безопасность данных и не выдавай будущие функции за готовые.
