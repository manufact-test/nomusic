# SUPERSEDING RESULT — LaC7 owner resolution, 15 Nov 2026

**Repository:** `manufact-test/nomusic`  
**Working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `f860ab79d98bda49469a5ce7f9a4d4005c7976b2`  
**CI:** [#43747724142](https://github.com/manufact-test/nomusic/actions/runs/43747724142) — SUCCESS, 91/91 tests; exact issuer-signed 2025 original, six DEX inspected read-only.  
**Exact green backup:** `backup/android-a1-lac7-owner-audit-ci-green-20261115` @ `f860ab79d98bda49469a5ce7f9a4d4005c7976b2`.  
**Runtime hooks:** unchanged; no APK built, patched, or released.

## LaC7 result

- `LaC7;` is defined in the signed DEX as an abstract interface.
- It has 8 direct implementers and no direct subclasses: `LIz4;`, `LOG8;`, `LWo4;`, `LaC7$a;`, `LbC9;`, `Lc6b;`, `LyEa;`, `Lyw9;`.
- Seven concrete `if(): Track` method bodies were found in the scoped implementers/ancestry.
- Only `LyEa.if(): Track` produced a typed identity trace: it reads a Track-typed field from `this` and returns that same object.
- `LyEa` has a Track-typed field, but its owner profile does not establish Player, MediaSource, decoder, or active-playback ownership.
- No runtime dispatch from the LCK1 callsite to `LyEa` is proven. The other six method bodies produced no typed Track identity event in this tracer; do not infer their return source from that absence.

**Gates remain:** `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`, `runtime_dispatch_proven=false`. This is a candidate only, not a Stage B success.

## Next bounded task — LyEa only

1. Inspect the exact `LyEa` constructor(s) accepting Track and prove whether the same Track parameter is stored into the field later returned by `LyEa.if()`. Keep field names and values out of the report.
2. Find only direct `new-instance LyEa` / constructor callsites. Trace the Track argument's object identity to its immediate origin and classify the owner by exact type/field/call contracts.
3. Inspect the exact LCK1 callsite to `LaC7.if(): Track`. Determine whether its receiver can be proven to be the same `LyEa` object. A class implementing the interface is not proof of runtime dispatch.
4. If the LyEa instance and Track cannot be tied to the active selected item, close this route as an unproven candidate and return to the already documented bounded audio-sink caller audit. Do not broaden to all eight implementations again.

## After closing LyEa

Continue from the existing native sink path: callers of `LcLb.O` and `Lbd6.O`; distinguish active playback from queue/prefetch/download; connect Track/Album to the sink only through bounded Java object identity; establish edition/generation for that same item; then prove the same identity at decoder/audio renderer. Only after that may the existing CELIKOM resolve/entitlement contract be connected before decoder input with the original native fallback.

## Unchanged hard constraints

Read-only and fail-closed. No generic runtime hooks, APK changes/builds/releases, login, account/media access, field values, Track/Album names or IDs, URLs, DataSpec, tokens, or audio bytes. No vendor method behavior changes or exception suppression. Do not touch NAV17, original Yandex, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB, or production. Do not request owner action unless a concrete necessary read-only measurement is first identified.

---

# CURRENT RESTORE POINT — 15 Nov 2026, CELIKOM Android A1

**Repository:** `manufact-test/nomusic`  
**Only working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Branch HEAD before this documentation update:** `e159fc02ad4b746647d417b065daa5791cdcf315` (three documentation-only commits ahead of the code checkpoint below; no code changes after the green audit).  
**Latest code checkpoint:** `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**Exact green code backup:** `backup/android-a1-lck1-predicate-audit-ci-green-20261115` @ `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**Latest CI:** [#43745289143](https://github.com/manufact-test/nomusic/actions/runs/43745289143) — SUCCESS, 88/88 tests; exact publisher-signed 2025 original, 16 splits / 6 DEX.  
**Last runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; subsequent work was read-only static audit and documentation.

## Product status — preserve these boundaries

- **Stage A = PASS on NAV17:** owner confirmed real Yandex account, albums, My Wave and original-track playback. This success must not be disturbed.
- **Stage B = NOT CONNECTED / NO-GO:** CELIKOM replacement audio is not connected or audible. No release APK from this research branch.
- Gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Latest LCK1 result

- `Lv3.throws(Track, Track)` delegates to `Objects.equals`; close it as a pure equality predicate.
- `LwEa.for(Track)` contains only the Kotlin non-null parameter check.
- `LHv4.if(Track)` was already bounded to parameter validation only.
- Neither inner coroutine proves passing the original field-backed Track to `LHl4.emit`.
- `LaC7.if(): Track` is the only remaining narrow reference: it supplies a second Track for comparison, but its exact owner/method resolution is not yet established.

## Next bounded task — do only this

1. Inspect the exact signed-DEX owner `LaC7;`: defined or absent, interface/class, abstract or concrete, superclass and interfaces.
2. If the exact `if(): Track` body is absent/abstract/inherited, enumerate only direct implementers or subclasses and trace only concrete implementations of that exact signature (including the nearest inherited method owner where needed).
3. Determine whether the returned Track is structurally sourced from player/current-source/decoder state. Do not infer this from names or type similarity.
4. If no concrete implementation exists in the pinned signed DEX, close this path as external/unresolved and return to the previously identified native audio sink caller path. Do not reopen closed LCK1 predicates or generic Flow collectors.

## After closing LaC7

Resume only the existing bounded audio-sink route: callers into `LcLb.O` and `Lbd6.O`; distinguish active playback from queue/prefetch/download; connect Track/Album to the sink only by bounded Java object identity; establish edition/generation for that same item; require the same identity at decoder/audio renderer. Only after that may the existing CELIKOM resolve/entitlement contract be connected before decoder input, with the original native fallback.

## Hard constraints

Read-only and fail-closed until the chain is proven. No generic runtime hooks, APK changes/builds/releases, login, account/media access, field-value/ID/name/URL/DataSpec/token/audio-byte reads, vendor behavior changes, or exception suppression. Do not touch NAV17, original Yandex, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB or production. Do not ask the owner for manual steps unless a concrete, necessary read-only measurement has first been identified. Work in large bounded blocks and preserve exact backups.

---

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

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 established the real owner flow; the owner reported audible original Yandex playback after login, with albums and My Wave visible. The diagnostic TXT does not independently verify the audio output. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

- Static audit code: `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Audit CI: [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) **SUCCESS**, 40/40 focused tests; verdict `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.
- Exact CI-green code backup: `backup/android-a1-audio-buffer-identity-ci-green-20261115` @ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Pre-fix rollback: `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`.
- Last runtime Java hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. This pass changed only the read-only static audit and its tests; no runtime hook, APK, account, phone or production component changed.

### Exact signed-DEX findings

- `LbJ2` implements `Lpk0` and declares typed `AudioTrack` and `ByteBuffer` fields. Its method named `native(ByteBuffer, long, int)` is the concrete ByteBuffer entry candidate; the same owner also exposes the AudioTrack construction/control path (`play`, `pause`, `flush`, AudioTrack factory methods).
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

