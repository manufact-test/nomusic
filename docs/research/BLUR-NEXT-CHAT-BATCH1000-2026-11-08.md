# CELIKOM Blur — handoff на следующие 200 после batch800 (08.11.2026)

**Читать первым:** [BLUR-BATCH800-2026-11-08.md](BLUR-BATCH800-2026-11-08.md), включая реальные отчёты Actions, состав и баланс исходника.

## Состояние
- Repo `manufact-test/nomusic`; отдельная актуальная ветка `feature/blur-batch800-20261108`; не трогать `main`/Android/Windows/extension.
- В production реально импортировано **200 новых pending**: replacement IDs **918–1117**, batch 4×50, source 1 306 322 832 байта, проверка 200/200 PASS, ни одного автоодобрения. [Импорт SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42513148392), [независимый audit SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42514057760).
- Предыдущие **718–917** после ручного одобрения владельцем: 200/200 approved/active, HEAD и Range 206 PASS. [Audit](https://github.com/manufact-test/nomusic/actions/runs/42512592398).
- Живая БД после batch800: **1108 Yandex tracks**, **908 active**, **200 pending**, **1112 локальных аудиоассетов** (реестр), **6 985 875 410 байт** в audio_assets; 1113 track_replacements всего (дополнительно 2 rejected, 3 disabled).
- Исторически импортировано по потоку FckCensorData **975 песен** (5+20+50+100+200×4). Партии 200x4 — 800 новых. CSV технических отказов теперь **73**.
- Source pinned FckCensorData commit `10187b7af56f311fe141a3c9b75483798bf0f589`: 1526 source files, после live-дедупа и текущего импорта осталось **384 не проверенных кандидата**, это НЕ 384 гарантированно валидных MP3. Дополнительно 73 технических отказа и 34 источника вне проверенного manifest.

## Следующий блок

1. **Сначала** после сообщения владельца о ручном одобрении batch800 сделать независимый read-only audit IDs 918–1117: все approved/active, каталог, resolve, signed HEAD/GET Range и точный byte check. Для подготовки можно адаптировать `tools/blur-batch600/check-current200-after-approval.php` по immutable [fixed-plan800.json](../../tools/blur-batch800/fixed-plan800.json).
2. По следующей команде создать новую изолированную ветку от batch800. Не переносить прежний fixed-plan в новую партию, не запускать прежний deploy.
3. Продолжать прежний `tools/blur-batch800/` импортёр. Исключить **73** cumulative rejected Track IDs, live SELECT по tracks/replacements/requests/tombstones, title+artist. Из ещё неиспользованных 384 кандидатов проверить MIME, Git blob, size, Mp3Inspector, ffprobe; временные ошибки отдельно. Если не удаётся собрать **ровно 200**, не загружать частичный произвольный набор и сообщить дефицит.
4. Записать новый `fixed-plan` ДО production и провести 4×50 с проверкой каждой партии, по окончании — отдельный независимый аудит. Отметку прав и approve выполняет только владелец.
5. Всегда докладывать фактическое количество активных/pending, assets и оставшихся кандидатов по живому production, с ссылками на CI. Не подменять юридические права технической пригодностью MP3.

**Внимание:** в batch800 первая версия preflight содержала опечатку `batch_size==73`, а первая версия независимого audit workflow ссылалась на `fixed-plan600.json`; обе исправлены, финальные прогоны SUCCESS. При переносе workflow заменять не только пути `blur-batch800/`, но и старое имя `fixed-plan800.json`, числовые суммы и число CSV-отказов; запускать независимый postcheck только **после** SUCCESS импорта.
