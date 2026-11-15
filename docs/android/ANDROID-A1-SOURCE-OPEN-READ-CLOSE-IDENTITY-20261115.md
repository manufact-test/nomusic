# CELIKOM Android A1 — read-only DataSource.open → read → close integrity, 15.11.2026

**Сохранено только в исследовательской ветке** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Не выдавать лабораторный код за продукт, не устанавливать на телефон без разрешённой проверки. Stage A = **NO-GO**, CELIKOM replacement = **NOT_CONNECTED**.

## Проблема после Fp0/RAa

Прежняя цепочка `native Track Flow → Gp0.new (Fp0) → tCa → download2.o.for (RAa) → Exo descriptor → Exo factory → RetryingBalancingDataSource → read` имела три диагностические неоднозначности даже при совпадении Java identity:
- Положительный `read()` мог засчитываться как связанный с Track, даже если **успешный `open()` этого же источника в этой lineage не наблюдался**.
- Несколько чтений одного source или повторное связывание того же Java source объекта могло выглядеть как много независимых доказательств.
- После неуспешного `open()` или `close()` старый флаг открытия мог оставаться валиден. Также поиск link в hot path мог повторяться без верхней границы, если ни один source не находился.

## Что поправлено

1. `StageBAudioEvidence.java`: флаги `sourceOpened` и `sourceReadAfterOpen` **на каждой точной Track→wrapper→descriptor→factory→source lineage**. Они очищаются при любом изменении wrapper/descriptor/factory/source. Только успешный original `open`, вызванный перед связанным положительным `read`, допускает `TRACK_SOURCE_READ_LINK`.
2. Новые bounded показатели `TRACK_SOURCE_UNOPENED_READ` (чтение есть, но open-proof нет), `TRACK_SOURCE_DISTINCT_POSITIVE_READ` (bounded weak `==` множество физических источников, не число чтений), `TRACK_SOURCE_CLOSE_LINK`, `TRACK_SOURCE_READ_SCAN_EXHAUSTED`. Ни ID, ни URL, ни audio bytes/offsets/headers/account не собираются.
3. `onExoSourceInstanceOpenAttempt` вызывается **до** неизменённого vendor `open`; отключает прежний open-proof, поэтому неудачный повторный open не оставляет ложной связи. После реального успешного `open` этот proof восстанавливается. Дедупликация физического source сохраняется при rebind.
4. Выявлен точный `RetryingBalancingDataSource.close()V` внутри 6 publisher-signed DEX 2025.10.4. [Static audit #43698830014](https://github.com/manufact-test/nomusic/actions/runs/43698830014) **SUCCESS**, `exo_source_class_present_in_signed_2025=true`, `exo_source_close_void_declared_in_signed_2025=true`. Отдельный read-only hook инвалидирует open-proof **до** неизменённого оригинального `close()`, даже если тот бросит исключение.
5. `read()` не выполняет неограниченный Java identity scan при отсутствии совпадающего источника: до **256** положительных source read-inspection callbacks на каждое новое связанное source-окно/reopen; после лимита явный показатель `SCAN_EXHAUSTED`. Это **семплирование**: NONE после лимита не доказывает отсутствие реального потока. `DataSource.read` всегда вызывает vendor оригинал ровно один раз без замены.
6. Unit/regression: чтение до open, успешный open→positive read, повторное read того же source, source rebind, failed reopen, source close, отличный source identity, bounded >256 unrelated reads. Summary теперь **44 строки**, последняя `CELIKOM_REPLACEMENT/NOT_CONNECTED`. PID-scoped parser теперь распознаёт `AUDIO_EXO_CLOSE_HOOK`.

## Безопасные контрольные точки

- До этого блока (точный исходный CI-green): `backup/android-a1-fp0-raa-dual-resume-ci-green-20261115` @ `2267c64f1df04b31a47f1a6e9d67b367ceea56db`.
- Прямой резерв перед open/read hardening: `backup/android-a1-source-read-after-open-pre-guard-20261115` @ `55d2f554a88b57d97323c4da878ccd0c2151c659`.
- Последний код этого блока: `9a22ec1e0b0fbd58bcf39e63fe61386514924681`.
- Clone-only ARM13 [#43699251424](https://github.com/manufact-test/nomusic/actions/runs/43699251424), publisher-first [#43699251417](https://github.com/manufact-test/nomusic/actions/runs/43699251417): **проверить конечный статус**. Предшествующий CI [#43698695680](https://github.com/manufact-test/nomusic/actions/runs/43698695680) SUCCESS относится к коду `0811345a` **до close hook**; нельзя переносить на актуальный код.

## Следующий проверяемый этап

1. Сверить оба CI по точному SHA и посмотреть отдельно `AUDIO_EXO_CLOSE_HOOK = REGISTERED` наряду со всеми 6 native Track/Fp0/RAa hooks и семью прежними Exo hooks. Регистрация не доказывает вызов `open/read/close`!
2. Реальная runtime цепочка требует same selected **track+album+edition+generation** на реальном native player preprepare и подтверждения источника на actual `read()`. Текущая Java reference lineage не означает «текущий играющий трек»: префетч/скачивание также может вызывать Exo DataSource.
3. Нет owner diagnostics после этого изменения; не требовать от владельца сборки, установки или ручных работ. Если сам пришлёт диагностику — первым делом разбирать счётчики; отличать **NOT_SEEN**, **NO_HOOK**, **NONE**, **SCAN_EXHAUSTED**.
4. Никаких изменений Test.50, frozen A1, Windows, расширения, backend, оригинальной Яндекс.Музыки/аккаунтов. Не считать Stage A готовым до реального аудио и подтверждения current source.


## Follow-up: позднее исключение vendor open()

Код `2dc2e1f0ad394f83bed27e2e2d272179e85441cd` добавляет отдельную обработку exception path: `onExoSourceInstanceOpenFailure(source)` вызывается при **реальном** исключении неизменённого `chain.proceed()`, принудительно ставит `sourceOpened=false`. Даже если более ранний конкурентный вызов вернул successful open, поздняя ошибка не даёт засчитать следующие reads. Original throwable немедленно пробрасывается наружу без подавления. Есть Java regression на поздний failure и последующий новый успешный open. Резерв перед исправлением `backup/android-a1-source-open-close-pre-failure-reset-20261115` @ `975ec09e3951f7d668d7de5d74be8450ccc0c2e5`. Проверить результаты [#43699883677](https://github.com/manufact-test/nomusic/actions/runs/43699883677) и [#43699883681](https://github.com/manufact-test/nomusic/actions/runs/43699883681); отсутствие исключений на CI без аудио — **не** текущий playback proof.
