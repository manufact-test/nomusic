# CELIKOM Windows W159 — owner test handoff (16 November 2026)

## Current state

The owner has downloaded Windows build **0.24.41.0** (native module **0.24.31**). The owner has **not yet confirmed installation or completed the acceptance check**. Download is not installation, and installation is not acceptance.

No new code change or package is requested at this point. The next chat must wait for the owner's actual test result before choosing further changes.

## Source of truth

- Repository: `manufact-test/nomusic`
- Product: CELIKOM Windows only
- Working branch: `main`
- W159 application code: `09fca7a0f7fb9b0f7fe4a436978c48968054a0fa`
- W159 owner-package source: `f9e82d9cce43fe0fb7949c51fe442bf37827f09b`
- Current documentation handoff commit: `c416f5edd170eaa9cc1008eda0277a0b4d206f99`
- Exact pre-W159 rollback: `backup/windows-main-pre-w159-mapped-source-status-20261116` @ `0e1de874bc15c401fcceb206511d8cb8f4005d80`

## Build and CI

- Owner build: **0.24.41.0**, native module **0.24.31**, internal unsigned owner-review build.
- W20 staging run: [43828713363](https://github.com/manufact-test/nomusic/actions/runs/43828713363) — SUCCESS.
- Artifact ID: `14208040930`.
- Main CI: [43828713432](https://github.com/manufact-test/nomusic/actions/runs/43828713432) — SUCCESS.
- Windows integration CI: [43828713415](https://github.com/manufact-test/nomusic/actions/runs/43828713415) — SUCCESS.
- Standalone installer: `CELIKOM-W159-MAPPED-TRACK-STATUS-02441-UNSIGNED.exe`, 85,133,124 bytes, SHA-256 `d378273712e1cb8876c4555d67dcabe1657d3359c87bd8969418c192b6f067e9`.
- ZIP: `CELIKOM-Windows-0.24.41.zip`, 84,653,314 bytes, SHA-256 `0322d19133d4c950940b6c06d856f5333677e6547b717a50c64dfb06783e166e`.
- ZIP was verified to contain exactly the same installer EXE as the standalone file, plus `SHA256SUMS.txt`.
- This is an internal unsigned test package, not a production release.

## What W159 changes

For a current track with an accepted CELIKOM mapping, compact popup and main window now use consistent neutral availability copy before/after VPN recovery and after Next:

- Header/service: `Сервис включён`.
- Current mapped track availability: `Версия CELIKOM доступна`.
- The false mapped-track warnings `Источник текущего трека не подтверждён` and `Ожидаем подтверждения` must not appear for that accepted mapping.

Do not weaken source proof. `Версия CELIKOM доступна` means the version/mapping is available; it does not prove the native decoder is outputting that source. `Подмена активна` and accent color remain gated by exact current native decoder proof.

## Owner acceptance still pending

The owner has said only that the new version was downloaded. Do not state that it is installed, tested, or accepted until the owner confirms.

The narrow acceptance check is:
1. Install/run 0.24.41.0 and play a track that has a CELIKOM version.
2. Note the main-window and compact-popup labels before VPN recovery.
3. Enable/reconnect VPN and wait for route recovery. Confirm the same mapped track keeps the same neutral availability/service labels.
4. Press Next to another track that also has a CELIKOM version. Confirm the labels remain consistent.

W158 VPN audio continuity was already manually accepted by the owner: the already-playing replacement continues through VPN route recovery without an audible pop or unnecessary restart. Do not reopen that investigation unless the owner reports a new audible regression.

If W159 passes, record owner acceptance and stop. No new build is needed.

If the owner reports a defect, analyze the exact observed state first. Make only the smallest relevant correction, preserve a rollback point, add a focused regression test, run only relevant tests and both CI workflows, and create at most one new owner package after a confirmed fix. Do not change playback/VPN/native code for a UI-only issue.

## Hard boundaries

- Do not restart from scratch or change architecture.
- Do not touch Android, browser extension, backend, Yandex original files, updater/P-256, W150 or unrelated work.
- Do not repeat the W54 diagnostic analysis or ask the owner to resend those already supplied captures.
- Do not run broad audits, unnecessary tests, or create intermediate EXE/ZIP packages.
- Do not start speculative changes before the owner's 0.24.41.0 test result.

## First message for the next chat

Привет! Принимай CELIKOM Windows после W159. Продолжай строго с текущего состояния, ничего не начинай с нуля и не меняй архитектуру.

Сначала прочитай:
- `docs/windows/W159-OWNER-TEST-HANDOFF-20261116.md` — актуальная передача и этот же текстовый handoff.
- `docs/windows/W159-MAPPED-TRACK-STATUS-20261116.md` — что именно исправлено в W159 и почему.
- `docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md` — история VPN/audio continuity и границы доказательств.

**Продукт:** только CELIKOM Windows.
**GitHub:** `manufact-test/nomusic`
**Единственная рабочая ветка:** `main`
**W159 код приложения:** `09fca7a0f7fb9b0f7fe4a436978c48968054a0fa`
**W159 source для owner package:** `f9e82d9cce43fe0fb7949c51fe442bf37827f09b`
**Текущий HEAD:** используй актуальный `main`; все последующие коммиты после W159 package source — только документация и не меняют код приложения.
**Точный rollback до W159:** `backup/windows-main-pre-w159-mapped-source-status-20261116` @ `0e1de874bc15c401fcceb206511d8cb8f4005d80`.

## Текущая версия и статус владельца

- Собрана одна внутренняя owner-review версия **0.24.41.0**, native module **0.24.31**.
- W20 run [43828713363](https://github.com/manufact-test/nomusic/actions/runs/43828713363) — SUCCESS; artifact ID `14208040930`.
- Main CI [43828713432](https://github.com/manufact-test/nomusic/actions/runs/43828713432) и Windows integration CI [43828713415](https://github.com/manufact-test/nomusic/actions/runs/43828713415) — SUCCESS.
- Владелец сообщил, что **скачал** новую версию. Установка и проверка пока НЕ подтверждены. Не записывай сборку как установленную или принятую.
- Не создавай новую сборку и не меняй код до результата проверки владельца.

## Что исправлено в W159

Одна и та же текущая mapped-песня после VPN recovery и после Next должна отображаться одинаково:
- верхний статус: `Сервис включён`;
- статус доступной версии: `Версия CELIKOM доступна`;
- ложные `Источник текущего трека не подтверждён` и `Ожидаем подтверждения` для уже принятого mapping не должны возвращаться.

Критически важно: `Версия CELIKOM доступна` — нейтральное подтверждение доступности/mapping, а НЕ доказательство декодирования. `Подмена активна` и акцентный цвет разрешены только при существующем точном подтверждении текущего native decoder source. Не ослабляй эту защиту.

## Что делать дальше

Сейчас не исследуй VPN/audio internals и не запускай широкие тесты. Дождись от владельца результата установки/проверки скачанной версии. Не проси повторно W54 diagnostics — они уже разобраны и сохранены в документации.

Владелец проверяет только:
1. На одной песне с доступной CELIKOM-версией — статусы до VPN.
2. После включения/переподключения VPN и восстановления связи — та же песня и те же статусы.
3. Нажать Next на другую песню, для которой также доступна CELIKOM-версия, — статусы должны остаться согласованными.

Звук при VPN continuity владелец уже вручную принял в W158: играющая подмена продолжает звучать без слышимого щелчка и ненужного перезапуска. Не открывай эту работу заново, если владелец не сообщит о новом слышимом дефекте.

Если проверка W159 проходит — зафиксируй owner acceptance в документации и остановись. Никакой новой сборки не нужно.

Если владелец сообщает о конкретном дефекте:
- сначала разберись в его описании, скриншотах и новой диагностике, если она есть;
- локализуй проблему в конкретном UI state/branch;
- не меняй playback/VPN/native путь, если проблема только в тексте/цвете;
- перед правками сохрани точку отката;
- добавь только релевантный регрессионный тест;
- прогони минимально необходимые проверки и оба CI;
- новую owner-сборку делай только после подтверждённого исправления и только одну, если без неё нельзя проверить результат;
- обнови документацию и следующий handoff.

**Запрещено:** начинать Android, browser extension, backend, Yandex original files, updater/P-256, W150 или архитектурный рефакторинг. Не делать массовых аудитов, лишних тестов, промежуточных EXE/ZIP и не повторять уже завершённую VPN-работу.

Главное сейчас — получить реальный результат проверки 0.24.41.0, а не придумывать следующую техническую задачу заранее.
