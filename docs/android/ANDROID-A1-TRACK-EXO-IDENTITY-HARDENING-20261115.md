# CELIKOM Android A1 — Track → Exo identity evidence hardening (15.11.2026)

**Stage A = PASS (NAV17 owner real Music flow). Stage B = IN PROGRESS. Исследовательский код, не релиз; CELIKOM replacement ещё не подключён.** Продолжение существующего одноплеерного native Yandex A1, без подмены источника. Исходный Android, Test.50, frozen A1, Windows, extension, backend и production не затронуты. Владелец ничего не устанавливает.

## Изменение кода

- Commit `f7983590bee3eec38ee8b09fd41859b64192f2df` (на текущей исследовательской ветке); immutable pre-change backup `backup/android-a1-track-exo-identity-pre-hardening-20261115` @ `746abe055b4bf903e3d280834e7cf432a0b1bd96`.
- `StageBAudioEvidence.java`: scoped request frames теперь сохраняют null как **запрет перехода к внешнему кадру**. Слабая ссылка, очищенная GC, тоже не разрешает брать identity из внешнего кадра. Вложенный `Gp0.new` или `download2.o.for` с null не может ошибочно присвоить результат чужому Track.
- При новой сборке `tCa` для Track очищается прежняя цепочка descriptor/factory/source. При новом descriptor очищается factory/source, при новой factory очищается source. Повторный read старого source не засчитывается как read нового Track.
- `findByWrapper/findByDescriptor/findByFactory/findBySource` возвращают только **однозначное** совпадение идентичности `==`, при двух совпадениях fail-closed. Никакие строки Track, URL, токены, данные аккаунта и аудиобайты не читаются/экспортируются.
- Два новых ограниченных raw-счётчика `NATIVE_TRACK_WRAPPER_CONSTRUCTED` и `NATIVE_MAIN_SOURCE_ENTER` позволяют различить «метод не выполнялся» и «метод выполнялся, но identity не связалась».
- `test_a1_stage_b_audio_evidence.py`: JVM regression для nested null scope, повторной постройки, устаревшего descriptor/factory/source, коллизии одного descriptor у двух Tracks. Формат summary теперь 34 строки (вместо 32), `CELIKOM_REPLACEMENT / NOT_CONNECTED` по-прежнему последняя строка.

## Следующая реальная диагностика — читать **сначала счётчики**, а не REGISTERED

1. `NATIVE_TRACK_FLOW_EMIT` → `NATIVE_TRACK_SOURCE_REQUEST` → `FLOW_TRACK_SAME_OBJECT` — был ли вообще вход с тем же Java Track.
2. `NATIVE_TRACK_WRAPPER_CONSTRUCTED` при `TRACK_WRAPPER_LINK = NONE` — конструктор исполнялся, но сохранённой identity активного Track нет.
3. `NATIVE_MAIN_SOURCE_ENTER` при `WRAPPER_MAIN_SOURCE = NONE` — source-builder был вызван, но его wrapper не совпал с track-linked wrapper.
4. `EXO_DESCRIPTOR_BUILT` при `WRAPPER_DESCRIPTOR_LINK = NONE` — дескриптор наблюдался, но не в подтверждённой текущей wrapper-scope.
5. `EXO_FACTORY_CREATED` → `TRACK_DESCRIPTOR_FACTORY_LINK` → `TRACK_FACTORY_SOURCE_LINK` → `TRACK_SOURCE_OPEN_LINK` → `TRACK_SOURCE_READ_LINK`. Пропавший шаг локализует только *первую недоказанную identity-связь*, а не доказанную потерю звука.

Счётчики `NONE/ONE/FEW/MANY` обобщённые, не trackId и не количество успешных композиций. Все эти связи могут отражать предзагрузку/загрузку, а не текущую audible дорожку.

## Важное ограничение по coroutine

Issuer-signed read-only audit #43648001634 на оригинале 2025.10.4 показал внутри `Gp0.new` потенциально приостанавливаемый вызов `Hp0.const(..., Oe2)` (ordinal 39) **перед** `tCa(String)` ctor (ordinal 63). `download2.o.for` тоже имеет continuation и вызывает descriptor-builder. При suspend/resume ThreadLocal-связь может завершиться до возобновления, либо аргументы возобновлённого кадра могут отличаться. Поэтому `TRACK_WRAPPER_LINK = NONE` или `WRAPPER_DESCRIPTOR_LINK = NONE` пока может означать coroutine-разрыв наблюдения, а не отсутствие реального Track или источника.

Отдельный signed audit сообщил `string_argument_origin=UNTRACED_STRING` для вызова `tCa(String)`: статическая same-method последовательность не доказывает branch-sensitive Track.field → String → wrapper. Не извлекать приватные поля/содержимое Track ради искусственно зелёного результата. Следующая работа — реальное разрешённое наблюдение bounded identity в source-before-prepare; без него **нет product pass и нет CELIKOM replacement**.

## CI

После изменения исходников запущены [clone-only ARM13 #43654168986](https://github.com/manufact-test/nomusic/actions/runs/43654168986) и [AppMetrica lifecycle ARM13 #43654169076](https://github.com/manufact-test/nomusic/actions/runs/43654169076). Clone-only #43654168986 завершён **SUCCESS**, 25/25 на свежем Android 13 ARM, JVM и module checks green. Publisher и реальное audio отсутствовали. Publisher-first #43654169076 **SUCCESS**: оригинал (16/16 splits) и клон одновременно установились в disposable ARM13, исключения не подавлялись. Итог `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; Stage A остаётся NO-GO, `stage_b_current_player_album_edition_attested=false`, аудио/аккаунт не проверены. Исходные `#43649573590` SUCCESS / 25-25 относятся к **предыдущему checkpoint** `d8049537`, а не к `f7983590`. Нельзя переносить этот статус на новые исходники.


## Superseding technical checkpoint — 15 Nov 2026 (AudioTrack / ByteBuffer)

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 opened the owner's real Yandex Music account, showed albums and My Wave, and played original Yandex tracks on the handset. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

- Static audit code: `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Audit CI: [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) **SUCCESS**, 40/40 focused tests; verdict `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.
- Exact CI-green code backup: `backup/android-a1-audio-buffer-identity-ci-green-20261115` @ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Pre-fix rollback: `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`.
- Last runtime Java hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. This pass changed only the read-only static audit and its tests; no runtime hook, APK, account, phone or production component changed.

### Exact signed-DEX findings

- `LbJ2` implements `Lpk0` and declares typed `AudioTrack` and `ByteBuffer` fields. Its `native(ByteBuffer, long, int)` method is the concrete native audio-buffer entry candidate; the same owner also exposes the AudioTrack construction/control path (`play`, `pause`, `flush`, AudioTrack factory methods).
- Two direct class callsites pass the caller's exact ByteBuffer parameter to `LbJ2.native`: `LcLb.O(..., ByteBuffer, ...)` at ordinal 43 and `Lbd6.O(..., ByteBuffer, ...)` at ordinal 38. Both use the same caller parameter register (v6); the bounded register-write census found no write to it, and the invoke word map correctly accounts for the wide `long` argument occupying two register words. This is a static same-register provenance result, not runtime playback proof.
- `LEF2.j()` calls the exact `Lpk0.native(ByteBuffer, long, int)` interface reference and passes a ByteBuffer read from a typed field. `LbJ2` implements `Lpk0`, but the audit does not infer the runtime interface receiver/dispatch or prove that this is the same object as either direct class callsite.
- Branch handling now preserves a caller ByteBuffer parameter only when its original register is not written anywhere in the method (including the second word of wide writes). Other aliases are discarded at branch joins; the audit deliberately prefers false negatives over path-insensitive identity claims.
- Invoke mapping now expands `J`/`D` into two register words and reports both logical argument positions and register-word positions. Static and instance/interface invocation fixtures are separately tested.

### What remains unproven

`active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. We have not connected this ByteBuffer to the current selected Track, its Album, edition/generation, or the exact same item observed at the native decoder/audio renderer. No CELIKOM source resolver is wired into this path; no replacement source is selected. The audit does not read ByteBuffer contents, Track/Album field values, names/IDs, URLs, DataSpec, account data, tokens or audio bytes.

### Next work

1. Trace the actual caller/owner path into `LcLb.O` and `Lbd6.O`; distinguish active playback from queue, prefetch and download. Keep virtual/interface dispatch and coroutine resume uncertainty explicit.
2. Join the proven audio-buffer sink path to the exact Track/Album identity only by bounded Java object identity. Do not infer it from method names, timing or matching types.
3. Establish a distinct edition/generation identity for that same selected item. Numeric fields and collection fields alone are not semantics.
4. Require the same selected identity at the decoder/audio renderer. Only then connect the existing authorized CELIKOM resolve/entitlement contract before decoder input, preserving the single native player and original fallback.
5. Do not ask the owner for another login, APK install or manual diagnostic until a concrete read-only measurement is identified.

