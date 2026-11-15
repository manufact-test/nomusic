# CELIKOM Android A1 — read-only DataSource.open → read → close integrity

**Current status — 15 November 2026:** latest code/static audit checkpoint 90f8ea394e1ac4168aa63f976e17fd18eb24befb; active branch experiment/android-a1-metrica-init-state-observer-arm13-20261112. The current Track/Album identity bridge is described in ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md. Publisher-first CI #43703211345 and clone-only CI #43703211359 both succeeded for the runtime hook code, but this is lab registration/stability only. Stage A remains **NO-GO**; audio/current selected Track/edition/decoder are not proven. Historical lifecycle notes follow; newer status above supersedes earlier checkpoint references below.

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

## Принципиальная регрессия (дополнение `9af55e5909592021f75b69d7b4d1b5cec2252cfc`)

Исправлены недостаточные прежние Java-тесты: счётчик DISTINCT не мог обнаружить, если `TRACK_SOURCE_READ_LINK` ошибочно увеличился уже после `close` или failed reopen. Теперь **три отдельных Java fixture** создают точные `Track → wrapper → descriptor → factory → source` ссылки; после close, vendor open failure и rebind требуют `TRACK_SOURCE_READ_LINK=NONE` и `TRACK_SOURCE_UNOPENED_READ=ONE`, затем после нового successful `open` требуют `TRACK_SOURCE_READ_LINK=ONE`. Дополнительный тест не меняет наблюдатель/Яндекс, лишь проверяет fail-closed семантику. Clone-only CI [#43700267919](https://github.com/manufact-test/nomusic/actions/runs/43700267919) проверить отдельно.

`2dc2e1f0ad394f83bed27e2e2d272179e85441cd` — последний **исполняемый** код, `9af55e59` — последний Java regression checkpoint. Даже если CI green, ни linked source, ни audio/decoder/current Track реально не проверялись в clone-only.

## Подтверждённый CI-green итог для исполняемого кода `2dc2e1f0`

- [Clone-only ARM13 #43699883677](https://github.com/manufact-test/nomusic/actions/runs/43699883677): **SUCCESS**, стабильные 25/25, Java regression/module сборка прошли, шесть native-track и восемь source hooks REGISTERED. Original intentionally absent, audio/login не тестировались.
- [Publisher-first ARM13 #43699883681](https://github.com/manufact-test/nomusic/actions/runs/43699883681): **SUCCESS**, 16/16 publisher source splits и клон установлены одновременно, no-suppression, `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `stage_a=NO_GO`, `stage_b_current_player_album_edition_attested=false`.
- Immutable code backup: `backup/android-a1-source-open-read-close-lifecycle-ci-green-20261115` @ `2dc2e1f0ad394f83bed27e2e2d272179e85441cd`. Отличать от текущей исследовательской ветки с документацией и дополнительными тестами.
- Подробный fail-closed Java fixture дополнен отдельными fresh linkage cases в коммите `9af55e5909592021f75b69d7b4d1b5cec2252cfc` (исполняемый observer не менялся). [Проверка clone-only #43700267919](https://github.com/manufact-test/nomusic/actions/runs/43700267919) на момент записи была ещё не завершена, Java regression phase уже прошла. Нельзя считать этот run SUCCESS до итогового статуса.

Даже все зелёные tests являются **регистрацией и лабораторной устойчивостью**, не product pass: нет допущенного current selected Track, exact album/edition/generation decoder pre-prepare и реального audio DataSource.read в воспроизведении.


## Track/Album identity follow-up — 15.11.2026

Подробная новая передача: docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md.

- Signed DEX audit [#43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959) SUCCESS: Track model has one Album-typed field; two constructors accept an Album argument. Direct same-object write from constructor argument into Track's own Album field was **not** proven. One exact Track copy method accepts Track+Album, reads the source Track's Album field, passes an Album argument to a Track constructor and returns a Track; static flow is explicitly a **candidate**, not proof for every branch.
- Runtime hooks AUDIO_NATIVE_TRACK_ALBUM_HOOK and AUDIO_NATIVE_TRACK_ALBUM_COPY_HOOK both REGISTERED in clone-only and publisher-first ARM13 CI.
- StageBAudioEvidence carries only weak Track/Album references with Java ==, bounded maps; no field reflection, album values, titles, IDs, URLs, account values, tokens or audio bytes. It propagates the constructor/copy-associated Album identity through Track Flow → wrapper → descriptor → factory → DataSource → successful open → positive read.
- New summary rows: TRACK_ALBUM_CONSTRUCTOR_LINK, FLOW_TRACK_ALBUM_LINK, TRACK_WRAPPER_ALBUM_LINK, TRACK_DESCRIPTOR_ALBUM_LINK, TRACK_FACTORY_ALBUM_LINK, TRACK_SOURCE_ALBUM_LINK, TRACK_SOURCE_ALBUM_OPEN_LINK, TRACK_SOURCE_ALBUM_READ_LINK, TRACK_ALBUM_IDENTITY_CONFLICT. Summary length is now 53 rows; final AUDIO_STAGE_B_STATUS row is index 52.
- Both [clone-only #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359) and [publisher-first #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345) SUCCESS. Verdict is METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO; current Track/Album/edition is not attested and audio was not tested. Stage A remains NO-GO.
- The Album identity counters are diagnostic candidates only. Track Flow may represent queue/prefetch, not current audible selection. No edition/generation semantics or same-object decoder input path has been proven.


## Follow-up: selected-state / MediaSession / decoder boundary census — 15.11.2026

Latest static-audit code checkpoint: `8eb2e6a3bc61643219ddc2e261853f8a3bd4865f`. Runtime Java hooks were not changed; last runtime-hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. The new CI-green code backup is `backup/android-a1-track-return-callsite-ci-green-20261115` @ `8eb2e6a3bc61643219ddc2e261853f8a3bd4865f`. Pre-change backups: `backup/android-a1-selected-item-deeper-audit-prechange-20261115` @ `28cf873d8cc14cf6f62cafea0fb38fe9df3897e0`, `backup/android-a1-track-state-callsite-census-pre-20261115` @ `0cefeaa01b5f17aa455544d86064a288348e0baa`, and `backup/android-a1-track-return-callsite-pre-20261115` @ `15824db97162db20115da35ea41d80b98e1be814`. The earlier runtime/Album CI-green backup remains `backup/android-a1-track-album-publisher-first-ci-green-20261115` @ `90f8ea394e1ac4168aa63f976e17fd18eb24befb`.

### Final static findings on the exact pinned signed 2025.10.4 #120.1gpr six-DEX original

- [MediaSession / decoder boundary scan #43705414957](https://github.com/manufact-test/nomusic/actions/runs/43705414957): SUCCESS.
- [Typed boundary callsite census #43705670723](https://github.com/manufact-test/nomusic/actions/runs/43705670723): SUCCESS.
- [Track-returning helper census #43705962875](https://github.com/manufact-test/nomusic/actions/runs/43705962875): SUCCESS; 16/16 focused Python tests passed.
- MediaSession metadata: 1 unique method reference, 6 callsites in 5 caller methods. No Track/Album parameter, Track/Album field read, Track/Album model method call, or Track/Album-returning helper was found before those callsites.
- MediaSession state: 4 unique method references, 8 callsites in 7 caller methods. The same Track/Album relationships were absent.
- Decoder/render boundaries: 19 unique method references, 48 callsites in 38 caller methods. No Track/Album parameter, field read, model method call or Track/Album-returning helper was found before those callsites. Seven callsites read an integer/wide field from their own receiver; this is not evidence of a generation counter.
- No explicit Edition/Generation type descriptor or named/typed Edition/Generation field was found on the native Track or Album models. This is a bounded static result, not proof that no obfuscated or indirect representation exists.
- Direct Track-parameter flow into public Player selection/transport, MediaSession, decoder boundaries and the native descriptor builder: zero. The single direct Track-to-source call remains the known download/source-descriptor coroutine candidate; it is not proof of the currently selected player item.
- Existing Album constructor/copy result remains unchanged: one Album-typed field on Track; two Track constructors accept Album, but direct same-object storage into Track's own field is not proven. One Track+Album→Track copy candidate reads the source Track's Album field, passes the Album argument to a Track constructor and returns Track; storage on the returned Track is not proven.

### Scope and interpretation

This is same-method static structure only. It does not infer virtual receiver selection, branches, coroutine resumption, reflection, cross-method alias flow, current playback state or audio output. It does not read runtime field values, album names/IDs, URLs, DataSpec values, account data, tokens or audio bytes; the final census does not scan arbitrary DEX strings. Do not treat zero direct links as proof that no indirect path exists.

No runtime hook was added or changed, no APK was built or published, no owner phone/account was touched, and no playback/audio test was run. Stage A remains **NO-GO**; `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

### Next bounded research block

1. Inventory all classes that declare a Track-typed field and their structural relationship to player/source owners; do not assume a field means current selection.
2. Trace Track-typed values returned by helper methods across one bounded caller edge, with register identity and branch/coroutine uncertainty explicitly marked.
3. Only add a read-only runtime hook after a concrete player-state owner and exact method/callsite are identified. Do not add generic MediaSession/MediaCodec hooks as substitutes.
4. Keep edition/generation unclaimed until a distinct object or stable generation boundary is structurally linked to the same Track and Album.
5. Continue to require the same identity at actual decoder input/audio renderer; a Track Flow or DataSource read remains insufficient.


## Superseding follow-up: class-level Track owner inventory — 15.11.2026

Latest static-audit code checkpoint: `22e468df44b45f7bcbebd6261f25df816ff6d0aa`. CI [#43706266458](https://github.com/manufact-test/nomusic/actions/runs/43706266458) is **SUCCESS**, with 18/18 focused Python tests passing. CI-green code backup: `backup/android-a1-track-owner-inventory-ci-green-20261115` @ `22e468df44b45f7bcbebd6261f25df816ff6d0aa`. The prior `8eb2e6a3` checkpoint and its backup remain valid historical checkpoints; no runtime hook was changed by either static-audit extension.

The exact pinned signed 2025.10.4 #120.1gpr six-DEX inventory found:

- 267 class owners with a Track-typed instance field; 127 with an Album-typed instance field.
- 14 owners have both Track- and Album-typed instance fields; 2 have both Track and the track-ID wrapper.
- Zero Track-field owners have a Player API field, implement the standard Player API, or have a MediaSession, decoder, source-like or Kotlin Flow field.
- 23 Track-field owners also have a collection field; 91 have an integer/wide numeric field. These are only structural categories: do not label them queue or generation without an actual dataflow proof.
- MediaSession and decoder boundary caller classes also have zero Track/Album field owners. Combined with the previous census, there is no same-method Track/Album parameter, field-read, model-method or Track/Album-returning-helper link before those boundaries.

This does **not** prove that no indirect player-state path exists: cross-method object aliasing, coroutine resumption, virtual receiver choice and reflection are not inferred. It does establish that no safe class-level Player/source owner has yet been identified from the pinned DEX. The single direct Track-to-source path remains the download/source-descriptor candidate, not current selection.

### Next bounded research block (supersedes the earlier inventory task)

1. Inspect the 14 shared Track/Album owner classes and the 2 Track/wrapper owner classes through one bounded caller edge; classify methods by typed parameters/returns and object identity, not names guessed from obfuscated symbols.
2. Trace whether a stable Track wrapper or returned Track object is handed to the actual player owner through a method boundary. Keep queue, prefetch and download candidates separate.
3. If no identity-bearing player owner emerges, do not add generic MediaSession/decoder hooks. A real playback witness will then be the only meaningful next measurement; do not ask the owner for manual steps or an APK install until the exact hook/callsite is known.
4. Edition/generation remains unproven. Numeric fields and collection fields are not semantic evidence.

Stage A remains **NO-GO**. No runtime hooks changed, no APK was built/published, no owner phone/account was touched, and no audio playback was tested.
