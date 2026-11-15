# АКТУАЛЬНЫЙ HANDOFF — CELIKOM Android A1, 15.11.2026

**Этот блок supersedes старые инструкции ниже. Не возвращаться к закрытой LyEa-ветке и не повторять уже выполненные аудиты.**

## Контрольная точка

- Продукт: **CELIKOM Android**, мобильное приложение. Не Windows и не браузерное расширение.
- Репозиторий: manufact-test/nomusic.
- Единственная рабочая ветка: experiment/android-a1-metrica-init-state-observer-arm13-20261112.
- Последний кодовый checkpoint: 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
- CI #151: [SUCCESS, 104/104](https://github.com/manufact-test/nomusic/actions/runs/43756845719), точный publisher-signed Yandex 2025 XAPK, шесть DEX, read-only.
- Точный резерв зелёного кода: backup/android-a1-renderer-field-cfg-trace-ci-green-20261115 @ 476bf5ee0751f2ba5851f41a0f2a82e2792cf9e8.
- Последний runtime-hook change: a655712d210189f3bc611847235de3ed4d985c1a. После него runtime hooks не менялись.
- Последний проход менял только статический анализатор и его unit-тесты. APK не собирался, не патчился, не устанавливался и не выпускался.
- После кодового checkpoint выполнены только docs-only commits; кодовый checkpoint остаётся указанным выше.

## Закрытая ветка LyEa / LaC7 / LCK1

CI #148 закрыл LyEa-кандидат как неподтверждённый маршрут. Не возвращаться к LyEa, LaC7 implementers/callers, LCK1 или unrelated LzA9 callers. Общая receiver identity не доказана; LzA9 exact method остаётся abstract interface без найденного тела.

## Renderer ByteBuffer CFG — точный результат

CI #151 добавил branch-sensitive trace только для LcC0.n(JJ)Z и Lkd6.n(JJ)Z. Разные CFG-состояния и альтернативные записи не объединяются.

- LcC0.n: Lad6.final result at pc 193 → field slot 2 store at pc 197 → same-this field read at pc 266 → virtual O call at pc 293. Второй call: тот же source/store → read pc 331 → O call pc 353.
- Lkd6.n: Lad6.final result at pc 170 → field slot 3 store at pc 174 → same-this field read at pc 232 → virtual O call at pc 259. Второй call: тот же source/store → read pc 282 → O call pc 304.
- Для каждого из четырёх sink-related callsites есть два distinct incoming CFG identity states: один сохраняет точную ссылку Lad6.final → field store → field read → virtual O call; второй приходит к тому же field read без доказанного writer origin в этом method.
- Следовательно, same Lad6 reference is proven only on one of two states per callsite. same_lad6_final_field_reference_on_every_state=false. Не объявлять цепочку непрерывной на всех ветках.
- Более поздние неизвестные записи в slot 2 / slot 3 находятся после этих callsites и не смешиваются с ними.
- O-вызовы являются virtual references с возможными sink implementations LcLb.O / Lbd6.O. Их ByteBuffer parameter → LbJ2.native(ByteBuffer, long, int) уже доказан, но runtime virtual dispatch на эти реализации не доказан.
- CFG trace не включает exception edges и не моделирует внешние field mutations/reentrant calls. Это method-local static identity, не доказательство активного playback.

Подробности и PCs: ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md.

## Текущий выбранный Track/Album — точный блокер

Уже имеющийся bounded signed-DEX census, без повторного сканирования:

- Прямых Track-parameter callsites в Player selection, MediaSession state/metadata, native descriptor или decoder boundary: 0.
- Среди 267 Track-field owners нет класса с Player API, MediaSession, decoder, MediaSource/source-like или Kotlin Flow field.
- 16 shared Track/Album или Track/wrapper owner candidates дали 44 method summaries и 16 inbound-caller summaries. Ни один из этих methods не вызывает Player API, MediaSession, decoder boundary или source descriptor.
- Два object-identity handoffs ведут только к конструкторам вспомогательных объектов: Track parameter → Track/Album constructor; Track + wrapper fields → continuation constructor. Ни один не устанавливает current selected Track.
- На Track/Album не найдено Edition/Generation type descriptor или typed/named field. Edition/generation identity остаётся неизвестной.

**Точный разрыв:** нет доказанного владельца именно текущего выбранного Track/Album и нет identity edge от такого владельца к decoder/render path. Очередь, prefetch, download и constructor candidates не считать playback.

## Статус продукта

- Stage A / NAV17: PASS по подтверждению владельца — нативный Яндекс, аккаунт, альбомы, Моя волна и оригинальное воспроизведение работают. Не ломать и не переигрывать.
- Stage B: **NOT CONNECTED / NO-GO**. CELIKOM-версии ещё не подключены к нативному декодеру и не звучат.
- active_selected_item_proven=false.
- same_native_item_to_decoder_proven=false.
- same_track_album_edition_generation_owner_proven=false.
- codec_output_object_to_audio_sink_proven=false.

## Следующее действие

Не добавлять runtime hooks, не менять APK/vendor-код и не расширять статический поиск на соседние классы. Не повторять writer census, shared-owner census, LyEa audit или CI.

Продолжать только при появлении конкретного identity-bearing witness текущего выбранного Track на точном Player selection callsite, который позволит связать тот же Track + Album + edition/generation с уже найденным decoder/render path. До такого witness — зафиксировать блокер и остановиться. Не просить владельца о ручных действиях без точного необходимого read-only измерения.

## Жёсткие границы

Не трогать оригинальный Яндекс, NAV17 auth/account, Test.50, frozen A1/LSPatch baseline, Windows, браузерное расширение, backend/API/DB и production. Не читать/экспортировать значения приватных полей, названия/ID треков и альбомов, URL, DataSpec, токены, данные аккаунта или аудиобайты. Не менять поведение vendor methods, не подавлять исключения, не добавлять второй плеер/декодер/AudioTrack.
# SUPERSEDING CHECKPOINT — CI #144, LyEa exact field and LCK1 receiver audit

**Repository:** \`manufact-test/nomusic\`  
**Only working branch:** \`experiment/android-a1-metrica-init-state-observer-arm13-20261112\`  
**Code checkpoint:** \`592ed5c2aa162bfb7e7ef659fbe6d0146703d461\`  
**CI #144:** SUCCESS, 97/97 tests — run \`43750484557\`. Exact issuer-signed 2025 original, six DEX, read-only.  
**Exact green backup:** \`backup/android-a1-lya-exact-field-lck1-receiver-ci-green-20261115\` @ \`592ed5c2aa162bfb7e7ef659fbe6d0146703d461\`.  
**Runtime hooks:** unchanged. No APK built, patched, installed, or released.

## Proven in this pass

- \`LyEa.if(): Track\` reads exactly one Track-typed instance field from \`this\` and returns that same object.
- Exactly one signed-DEX write to that same field was found. It is in \`LyEa.<init>(Track, ...)\`.
- The constructor signature accepts a Track parameter, but the identity tracer did **not** prove that the exact Track parameter is the value written to the field. Its exact field-store event had no Track identity origin. Do not infer parameter-to-field identity from the signature alone.
- Exactly two relevant \`LaC7.if(): Track\` callsites are in \`LCK1$c$a.emit\` and \`LCK1$h$a.emit\`.
- In both, the receiver origin is still unresolved. The exact field-read/constructor-parameter link was not established.
- \`LzA9.if()LaC7;\` appears as a common interface-object origin at 26 other callsites, but no code-bearing method definition was found under that exact signature in the signed DEX. It is not proven to return \`LyEa\`.
- The earlier broad scan found many unrelated \`LaC7.if\` callsites. Do not repeat that census.

## Gates — still closed

\`active_selected_item_proven=false\`  
\`same_native_item_to_decoder_proven=false\`  
\`runtime_dispatch_to_lya_proven=false\`

Stage B is not complete. The audit is structural only; it does not prove that the Track is the currently selected playing item or that it reaches the native decoder/audio sink.

## Next bounded pass — only these exact points

1. Inspect the source register of the single \`LyEa.<init>\` write to its Track field. Prove whether it is the constructor's Track parameter or another origin. Do not read/export field values.
2. Trace the receiver used by the two exact LCK1 \`LaC7.if()\` callsites across their local branch boundary. Limit the scan to \`LCK1$c$a.emit\`, \`LCK1$h$a.emit\`, their exact constructors, and the exact field refs they use. Track only object identity and type; include the concrete LaC7 implementer types where needed.
3. Inspect \`LzA9.if()LaC7;\` declaration/implementation only if one of those exact LCK1 constructor paths reaches it. Do not inspect its 26 unrelated callers.
4. If this does not produce one bounded identity chain from the actual selected Track to the LCK1 receiver, close this candidate and return to the existing native audio-sink caller audit (\`LcLb.O\` / \`Lbd6.O\`). No further broad interface or class census.

## Unchanged safety and scope

Keep NAV17 auth, original Yandex, account, playback, and data untouched. Do not change Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB, or production. No generic runtime hooks, no second player/decoder/AudioTrack, no private field values, Track/Album names or IDs, URLs, DataSpec, tokens, account data, or audio bytes. Do not suppress vendor exceptions or alter vendor method behavior. Do not request owner action unless a specific necessary read-only measurement is first identified.

---

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

# SUPERSEDING RESULT — 15 Nov 2026, LCK1 predicate/secondary Track source audit (CI GREEN)

**Code checkpoint:** `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.  
**CI:** [#43745289143](https://github.com/manufact-test/nomusic/actions/runs/43745289143) **SUCCESS, 88/88 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green backup:** `backup/android-a1-lck1-predicate-audit-ci-green-20261115` @ `09b4c989482413c7b0c74bbe49a83ed4b0ea4a7f`.

## Predicate results

- `Lv3.throws(Track, Track): boolean` delegates directly to `java.util.Objects.equals(Object, Object)`. This is a pure equality check; close it as a player/source/decoder path.
- `LwEa.for(Track): boolean` has only the Kotlin non-null parameter check in its body; no outgoing Track call edge.
- `LHv4.if(Track): boolean` likewise had only parameter validation in the prior bounded trace.
- `LaC7.if(): Track` is referenced by `LCK1$c$a.emit` as the source of a second Track compared against the exact retained Track, but the exact method reference is unresolved in the pinned signed DEX. Do not infer its behavior.

The branch-sensitive trace still proves that neither inner coroutine passes the original field-backed Track to `LHl4.emit(Object, Continuation)`.

## Next bounded task

Inspect only the exact owner `LaC7;`:
1. Establish whether the owner is defined in the signed DEX and whether it is an interface/abstract class.
2. If the exact `if(): Track` method is abstract/unresolved, enumerate only direct implementers/subclasses and trace concrete implementations of that exact signature.
3. Determine whether the returned Track is sourced from a player/source/decoder state. If no implementation exists in the signed DEX, close this handoff as external/unresolved.
4. Do not reopen the equality predicate or generic Flow collector branches.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, branch-sensitive inner Flow identity trace (CI GREEN)

**Verified code checkpoint:** `79e3399dd65806c4017f0077f406fdf0ef0b1265`.  
**CI:** [#43744778789](https://github.com/manufact-test/nomusic/actions/runs/43744778789) **SUCCESS, 88/88 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green backup:** `backup/android-a1-inner-flow-cfg-track-identity-ci-green-20261115` @ `79e3399dd65806c4017f0077f406fdf0ef0b1265`.  
**Previous green:** [#43744526981](https://github.com/manufact-test/nomusic/actions/runs/43744526981) SUCCESS, 87/87 tests; primitive argument false-positive guard verified.

## Branch-sensitive result

A bounded control-flow must-alias trace followed the exact Track field through all incoming branch states in the two inner Flow lambdas.

- `LCK1$c$a.emit`: reads the exact retained Track field; calls `Lv3.throws(Track, Track): boolean` with the field-backed Track as one argument. A separate `LaC7.if(): Track` call returns another Track. The subsequent `LHl4.emit(Object, Continuation)` call does **not** receive a proven alias of the original field-backed Track.
- `LCK1$l$a.emit`: reads the exact retained Track field; passes it to `LHv4.if(Track): boolean` and `LwEa.for(Track): boolean`. The subsequent `LHl4.emit(Object, Continuation)` call does **not** receive a proven alias of the original field-backed Track.

Thus neither inner coroutine proves emission of the original Track into the Flow collector. This branch is a predicate/filter path, not a proven player/source/decoder handoff. Do not describe it as playback or infer the collector's emitted value.

The audit now preserves aliases across branches only when the same exact origin is present on every incoming path. It rejects the proof if even one branch overwrites the register. Primitive DEX parameters are also excluded from object-identity evidence.

## Next bounded task

Inspect only:
- `LaC7.if(): Track` — exact source of the second Track returned in the LCK1$c$a predicate path;
- `Lv3.throws(Track, Track): boolean`;
- `LwEa.for(Track): boolean`.

`LHv4.if(Track)` was already traced and had no further same-Track call edge beyond parameter validation. If the three remaining methods only compare/filter Track metadata and do not reach a player/source/decoder boundary, close this entire LCK1 Flow branch and return to the previously identified native audio-output buffer path. Do not expand into generic Flow collectors or unrelated classes.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LCK1 Flow/coroutine field audit (CI GREEN)

**Code checkpoint:** `066778008331584301731f9d430a6713a0e7a02d`.  
**CI:** [#43743305204](https://github.com/manufact-test/nomusic/actions/runs/43743305204) **SUCCESS, 86/86 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-lck1-coroutine-field-audit-ci-green-20261115` @ `066778008331584301731f9d430a6713a0e7a02d`.  
**Previous audit-only run:** [#43743253472](https://github.com/manufact-test/nomusic/actions/runs/43743253472) SUCCESS, 85/85 tests.

## Exact Track field results

Each of these constructors stores the exact incoming Track into exactly one Track-typed field on `this`:
- `LJK1.<init>`: 1 field store; 4 methods read the exact field.
- `LCK1$a.<init>(Track, Continuation)`: 1 field store; 2 methods read the exact field.
- `LCK1$c.<init>(LC3a, Track)`: 1 field store; 1 method reads the exact field.
- `LCK1$l.<init>(LD3a, Track)`: 1 field store; 1 method reads the exact field.

Key exact same-Track outgoing edges:
- `LCK1$c.collect()` reads its exact Track field and passes that Track into `LCK1$c$a.<init>(LHl4, Track)`.
- `LCK1$l.collect()` reads its exact Track field and passes that Track into `LCK1$l$a.<init>(LHl4, Track)`.
- `LCK1$a.invokeSuspend()` passes the Track into `AbstractMap.containsKey(Object)`; this is a map-membership/filter candidate, not a player/source/decoder edge.
- `LUJ5.return(Track)` and `LHv4.if(Track)` expose no further Track-identity method handoff in the bounded trace (only parameter validation); do not chase them without new evidence.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Next bounded task

Trace only the two inner coroutine constructors:
- `LCK1$c$a.<init>(LHl4, Track)`
- `LCK1$l$a.<init>(LHl4, Track)`

Derive their exact Track field stores from the original Track parameter and scan only methods owned by those exact inner classes for reads of those exact field identities. Follow same-Track calls only toward Flow emission, source descriptor, player or decoder boundaries. Do not expand into generic Flow collectors or unrelated coroutine classes.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LCK1 Flow/coroutine Track path

**Code under CI:** `066778008331584301731f9d430a6713a0e7a02d`.  
**Prior green interface audit:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) SUCCESS, 85/85 tests, 16 signed splits / 6 DEX.  
**Current CI:** [#43743305204](https://github.com/manufact-test/nomusic/actions/runs/43743305204) — static tests/install phase; signed-DEX scan pending.  
**Previous code-only CI:** [#43743253472](https://github.com/manufact-test/nomusic/actions/runs/43743253472) — same implementation before the extra scope regression test; signed-DEX scan in progress.  
**Pre-CI backup:** `backup/android-a1-lck1-flow-coroutine-field-audit-pre-ci-20261115` @ `066778008331584301731f9d430a6713a0e7a02d`.  
**Previous green backup:** `backup/android-a1-lbk1-lgk1-interface-ci-green-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.

## Confirmed interface handoff

Both `LBK1` and `LGK1$a` are abstract interfaces in the signed original. `LBK1` has direct implementers `LCK1`, `LSV6`, `LXV6`; `LGK1$a` has 10 direct implementers. 42 exact method traces were captured.

The primary `LCK1` methods pass the same Track into:
- `LUJ5.return(Track): Flow`
- `LCK1$a.<init>(Track, Continuation)`
- `LCK1$c.<init>(LC3a, Track)`
- `LCK1$l.<init>(LD3a, Track)`
- `LHv4.if(Track): boolean`

`LXV6` delegates its five methods back to the `LBK1` interface refs. `LSV6` is a direct implementer but its exact concrete method bodies were not found in the prior bounded trace; the current owner profile output now includes its abstract/interface/superclass shape.

## Current bounded scope

The current code traces only the five exact LCK1 outgoing method refs and derives Track-typed fields written from the exact original Track parameter in constructors of `LJK1`, `LCK1$a`, `LCK1$c`, `LCK1$l`. It then scans only methods owned by those four classes for reads of those exact field identities. No field names/values are disclosed.

Next, read the report for:
- `LUJ5.return` and `LHv4.if` traces;
- constructor field-store counts and exact field-read method traces for each of the three LCK1 coroutine classes;
- `LSV6` implementer class shape.

If a coroutine reads the exact Track field and passes it to a concrete source/player/decoder boundary, follow only that edge. If it reaches only generic Flow construction, trace only the exact continuation/coroutine method that carries the same Track. Do not expand into unrelated implementers or generic player APIs.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LBK1 / LGK1$a implementation audit (CI GREEN)

**Code checkpoint:** `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**CI:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) **SUCCESS, 85/85 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-lbk1-lgk1-interface-ci-green-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.

## Interface findings

Both owners are defined abstract interfaces in the signed DEX:
- `LBK1`: 3 direct implementers — `LCK1`, `LSV6`, `LXV6`.
- `LGK1$a`: 10 direct implementers — `LHK1`, `LOIa`, `LU44`, `LZQ7`, `Lhe9`, `Lle9`, `LoC6`, `LuV2`, `LvG9`, `LyA8`.

42 exact implementation method traces were captured. Key `LBK1` implementation is `LCK1`:
- `LCK1.break(Track)` passes the same Track to `LUJ5.return(Track): Flow`.
- `LCK1.for(Track)` constructs `LCK1$a(Track, Continuation)`.
- `LCK1.new(Track)` constructs `LCK1$c(LC3a, Track)`.
- `LCK1.try(Track)` constructs `LCK1$l(LD3a, Track)`.
- `LCK1.this(Track)` passes the same Track to `LHv4.if(Track): boolean`.
`LXV6` is a delegating implementation whose five methods forward to the corresponding `LBK1` method refs. The exact `LSV6` implementation body was not present in the current bounded method trace; inspect its class shape before deciding whether it is abstract/delegating.

For `LGK1$a`, some implementers only forward the Track to generic Kotlin Function1/Function2 callbacks. More concrete callback paths include:
- `Lhe9` / `Lle9`: forward Track to three methods on `LVf9`.
- `LoC6`: forwards Track to `LLB6` methods.
- `LvG9`: forwards Track to `LpG9` methods.
These callback paths are secondary to the `LCK1` Flow/coroutine path unless the latter closes.

No field names or values were emitted. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Next bounded investigation

Prioritize the exact `LCK1` path:
1. Trace `LUJ5.return(Track): Flow` and `LHv4.if(Track): boolean`.
2. Inspect exact constructors `LCK1$a(Track, Continuation)`, `LCK1$c(LC3a, Track)`, `LCK1$l(LD3a, Track)`. Derive the exact Track-typed fields written from each original Track parameter and trace only reads of those exact fields in methods owned by those classes.
3. Follow only same-Track calls from those exact coroutine bodies toward a source descriptor, player or decoder boundary.
4. Check `LSV6` flags/superclass and do not fan out into all callback implementers unless the LCK1 path is closed.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LBK1 / LGK1$a implementation audit

**Code under CI:** `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**Last green signed-DEX audit:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) SUCCESS, 84/84 tests, 16 signed splits / 6 DEX.  
**Current CI:** [#43742534368](https://github.com/manufact-test/nomusic/actions/runs/43742534368) — parser/static tests SUCCESS; exact signed-DEX inspection in progress.  
**Pre-result code backup:** `backup/android-a1-lbk1-lgk1-implementation-audit-test-correction-20261115` @ `7e74639a06e4c6c2913fec3cd1c8c4a2e4ce7a69`.  
**Last green code backup:** `backup/android-a1-ljk1-exact-field-ci-green-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.

## Confirmed chain

- `LOW6.<init>` stores the exact Track and passes it to `LTv9.if`.
- `LTv9.if` passes the same Track to `LJK1.<init>`.
- `LJK1.<init>` stores the same Track in exactly one Track-typed field on `this`.
- Four `LJK1` methods read that exact field and pass the same Track to four `LGK1$a` methods:
  - `try(Context, Track)`
  - `case(Track)`
  - `else(Track)`
  - `goto(Track)`
- `LJK1.<init>` also passes the Track to four `LBK1` method refs returning Flow: `try(Track)`, `this(Track)`, `for(Track)`, `new(Track)`. The additional `LBK1.break(Track)` reference comes from `LOW6`.
- These `LBK1` and `LGK1$a` concrete method refs are now the only next focus.

## Current audit scope

The current commit adds:
- exact interface/abstract-class profiles for `LBK1` and `LGK1$a`;
- direct implementers or direct subclasses, plus their in-repository superclass method owners;
- exact concrete method traces only for the known five `LBK1` Track-to-Flow contracts and four `LGK1$a` Track callback contracts.

The method scan does not expand to unrelated methods/classes. Field names/values, media, URLs and account state are not emitted. CI parser/static tests passed; exact signed-DEX result is still pending.

## Next action after CI #43742534368

Read the interface owner map and exact implementation traces:
- If concrete implementations pass the same Track to a player/source/decoder boundary, follow only that exact edge.
- If an interface/abstract class has no in-signed-Dex implementation, trace only the exact constructor callsite that supplies that interface object, if necessary; do not fan out to unrelated implementers.
- If no direct same-Track path reaches player/source/decoder, close that branch and report the exact boundary.
- Keep `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false` until direct proof exists.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LJK1 exact field + LBK1 handoffs (CI GREEN)

**Code checkpoint:** `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**CI:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) **SUCCESS, 84/84 tests**, exact publisher-signed 2025 original verified (16 splits / 6 DEX).  
**Exact green code backup:** `backup/android-a1-ljk1-exact-field-ci-green-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Pre-CI retry backup:** `backup/android-a1-ljk1-exact-field-and-lbk1-handoffs-ci-retry-20261115` @ same code SHA.

## New signed-DEX findings

- `LJK1.<init>` stores the incoming Track parameter into exactly one Track-typed instance field on `this`.
- Four methods owned by `LJK1` read that exact same field on `this`: `break()`, `case()`, `if()`, `new()`.
- Those methods pass the exact field-read Track reference onward to `LGK1$a`:
  - `try(Context, Track)`
  - `case(Track)`
  - `else(Track)`
  - `goto(Track)`
- `LJK1.<init>` itself also passes the original Track parameter to four `LBK1` method references returning Flow: `try(Track)`, `this(Track)`, `for(Track)`, `new(Track)`.
- All five observed `LBK1` references in scope are unresolved as concrete method bodies in the pinned DEX (including `break(Track)` from `LOW6`). `LSV6.else` and `LSW6.if` are also unresolved. Do not infer their behavior.

No field names or values were emitted. These are static identity-preserving handoffs only; active selected playback and same-native-item-to-decoder are still not proven.

## Next bounded investigation

Inspect the exact contracts and direct implementers for `LBK1` and `LGK1$a`:
1. Establish whether each owner is an interface/abstract class and enumerate only its direct implementers.
2. For the four exact `LGK1$a` method signatures and four exact `LBK1` Track-to-Flow signatures, inspect only concrete implementations on those implementers (including superclass implementations where needed).
3. Trace the same Track parameter into an exact player/source/decoder boundary. If the interface has no concrete implementation in the signed DEX, record that as a closed boundary and do not fan out into unrelated classes.
4. Keep runtime and decoder gates false until the same native item is directly linked to the active player/source/decoder path.

No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT CHECKPOINT — 15 Nov 2026, LJK1 exact Track field + LBK1 recipients

**Code under CI:** `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Prior CI-green:** [#43740768063](https://github.com/manufact-test/nomusic/actions/runs/43740768063) SUCCESS, 81/81 tests; exact publisher-signed 2025 original 16 splits / 6 DEX.  
**Current CI:** [#43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839) — parser/static tests SUCCESS; exact signed-DEX inspection in progress.  
**Pre-CI code backup:** `backup/android-a1-ljk1-exact-field-and-lbk1-handoffs-ci-retry-20261115` @ `a4cd35290de8d5ff706a6ad7b740294d94c29af4`.  
**Previous green code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Confirmed chain before current CI

`LOW6.<init>(..., Track, ...)` stores the exact incoming Track and passes it to `LTv9.if(..., Track, boolean)`. The defined `LTv9.if` passes that same Track reference to `LJK1.<init>(..., Track, boolean)`.

CI #120 confirmed `LJK1.<init>` stores the exact Track parameter into a Track-typed field on `this`, then passes the same parameter to four methods on `LBK1`:
- `try(Track): Flow`
- `this(Track): Flow`
- `for(Track): Flow`
- `new(Track): Flow`

The current audit adds only those four exact method references to the bounded focus set and adds an internal exact-field matcher. It derives Track-typed field references stored from the original constructor parameter, then traces only reads of those exact field IDs from methods owned by `LJK1`. Field names and values are not emitted.

CI #121 failed only because the new test file had an escaped line-continuation syntax error. That was corrected in `a4cd352`; CI #122 parser/static tests passed. Do not revert working audit logic because of the prior syntax-only failure.

## Next action after CI #122

1. Read the report from [CI #43741676839](https://github.com/manufact-test/nomusic/actions/runs/43741676839).
2. If the exact Track field reads are found in LJK1 methods, follow only their same-Track outgoing calls. Separately inspect the four exact LBK1 recipient methods if they are defined in the signed DEX.
3. Follow only an exact same-Track identity edge into a concrete player/source/decoder boundary. If these paths end in Flow construction or unresolved interface methods, close them without expanding to generic APIs or unrelated owners.
4. Keep active selected item and same-native-item-to-decoder gates false unless directly proven.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. No runtime hooks, APK modifications, login, account/media access or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LJK1 Track continuation

**Previous CI-green code:** `70075818bb9965a98376f4cca30157a10bf746e8`.  
**Previous CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) **SUCCESS, 81/81 tests**, exact original 16 signed splits / 6 DEX.  
**New code HEAD:** `c9f218810392ba19e7c6997ed20ae3e7eaa6d059` — adds only the exact `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)` identity trace and its bounded-scope test.  
**Exact pre-CI backup:** `backup/android-a1-ljk1-constructor-pre-ci-20261115` @ `c9f218810392ba19e7c6997ed20ae3e7eaa6d059`.  
**Last green code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Last confirmed identity chain

`LOW6.<init>(..., Track, ...)` stores the exact incoming Track and passes it to `LTv9.if(..., Track, boolean)`. The defined `LTv9.if` passes the same Track reference to `LJK1.<init>(..., Track, boolean)`.

The other two referenced methods `LSV6.else(Track)` and `LBK1.break(Track)`, as well as the optional `LSW6.if(Track, boolean)`, are not defined in the pinned signed DEX. Do not infer behavior or chase them.

## Current bounded task

The new audit traces only `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`. On CI success:
- inspect whether the exact Track parameter is stored on `this` and whether it is passed unchanged to a concrete player/source/decoder boundary;
- if stored, trace only reads of that exact field from methods on `LJK1`, without disclosing its field name or value;
- if no relevant identity edge exists, close this branch rather than expanding into generic player APIs/Flow.

The latest code commit is not yet CI-verified at this handoff. No runtime hooks, APK, login, account/media access or vendor behavior change. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. NAV17 Stage A remains owner-confirmed PASS; Stage B replacement remains NOT CONNECTED / NO-GO.

---

# SUPERSEDING RESULT — 15 Nov 2026, LOW6 recipient trace (CI GREEN)

**Code checkpoint:** `70075818bb9965a98376f4cca30157a10bf746e8`  
**CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) **SUCCESS, 81/81 tests**; exact pinned publisher-signed original verified (16 splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-low6-recipient-ci-green-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Signed-DEX findings

From `LOW6.<init>(..., Track, ...)`, the same exact incoming Track reference is:
- stored in a Track-typed instance field on `this`;
- passed to `LTv9.if(..., Track, boolean)`;
- passed to method references `LSV6.else(Track)` and `LBK1.break(Track)`.

The pinned signed DEX defines `LTv9.if`, but does **not** define the referenced `LSV6.else`, `LBK1.break`, or `LSW6.if` methods. Those unresolved refs are closed as implementation candidates; do not infer their behavior.

Inside the defined `LTv9.if`, the same Track parameter is passed to:
`LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`.

This is an exact local object-identity edge, not proof that the object is the active selected player item. The return from `LTv9.if` is `LJK1`; no decoder/source/audio boundary was reached in this bounded trace.

## Exact next hop

Inspect only `LJK1.<init>(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`:
1. Verify whether the exact Track parameter is stored on `this` and/or passed unchanged to a concrete player/source/decoder method.
2. If stored, identify its field internally without exposing field name/value and trace only reads of that exact field from `LJK1` methods.
3. If no relevant outgoing identity edge exists, close this path; do not expand to generic player APIs or Flow implementers.

Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. Stage A NAV17 remains owner-confirmed PASS. Stage B replacement remains NOT CONNECTED / NO-GO. No release APK, runtime hook, login or media access.

---

# CURRENT IN-PROGRESS CHECKPOINT — 15 Nov 2026, LOW6 direct Track recipients

**Latest committed code:** `70075818bb9965a98376f4cca30157a10bf746e8`.  
**Previous CI-green signed-DEX result:** [#43739559516](https://github.com/manufact-test/nomusic/actions/runs/43739559516) SUCCESS, 80/80 tests; exact original verified (16 signed splits / 6 DEX).  
**Current audit CI:** [#43740254479](https://github.com/manufact-test/nomusic/actions/runs/43740254479) — in progress; this commit adds a single bounded hop from the exact Track handoffs observed in `LOW6.<init>`.  
**Intermediate audit run:** [#43740249574](https://github.com/manufact-test/nomusic/actions/runs/43740249574) was triggered by the parser-only commit immediately before the test-scope commit; prefer final result of #43740254479.  
**Exact code backup before this audit:** `backup/android-a1-low6-track-identity-pre-ci-20261115` @ `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Latest in-progress code backup:** `backup/android-a1-low6-direct-recipient-audit-pending-ci-20261115` @ `70075818bb9965a98376f4cca30157a10bf746e8`.

## Confirmed result from CI #118

The signed-DEX report established that `LOW6.<init>(..., Track, ...)`:
- stores the exact incoming Track parameter into a Track-typed instance field on `this`;
- passes that same Track reference to `LTv9.if(..., Track, boolean)`;
- passes that same Track reference to `LSV6.else(Track)`;
- passes that same Track reference to `LBK1.break(Track)`, whose declared return type is a Flow interface.

No field names or values were disclosed. The optional `LSW6.if(Track, boolean)` reference was not defined in the pinned signed DEX; do not infer it exists or use it as evidence.

These are exact local object-identity edges only. They do **not** prove active selected playback, player dispatch, decoder input or same-item audio output. Current gates remain `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

## Current bounded audit scope

The latest audit adds exact identity traces only for:
- `LTv9.if(LBK1, GK1$a, Context, CoroutineScope, Track, boolean)`
- `LSV6.else(Track)`
- `LBK1.break(Track)`

A regression test pins this exact five-entry focus set (including the optional unresolved LSW6 candidate and LOW6 constructor) so the audit cannot silently expand to generic callsites.

**Next action:** wait for CI #43740254479. On success, inspect only these three method traces. Follow only an exact same-Track call to a concrete player/source/decoder boundary. If no such call is present, close that recipient path and do not fan out into generic Flow or unrelated owners. On failure, retain the prior green checkpoint `70495580` and diagnose only the failing test/audit.

No runtime hooks, APKs, original Yandex/account/media access, or vendor behavior changes. NAV17 Stage A remains owner-confirmed PASS. Stage B replacement remains NOT CONNECTED / NO-GO.

---

# IN-PROGRESS CHECKPOINT — 15 Nov 2026, LSW6 / LOW6 identity trace

**Latest CI-green code:** `b250aba2ca5e7555995099683736be572f0ef578`, CI [#43738914218](https://github.com/manufact-test/nomusic/actions/runs/43738914218) SUCCESS, 80/80.  
**Current research HEAD:** `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Current CI:** [#43739559516](https://github.com/manufact-test/nomusic/actions/runs/43739559516) — still in progress at handoff.  
**Pre-CI code backup:** `backup/android-a1-low6-track-identity-pre-ci-20261115` @ `70495580be8a123cb3a209375fa233c7ee4879ae`.  
**Last fully documented CI-green handoff:** `backup/android-a1-ldt0-track-final-handoff-20261115`.

The only code change after the last green checkpoint adds read-only exact identity traces for:
- `LSW6.if(Track, boolean)`
- `LOW6.<init>(..., Track, ...)`

No runtime hook, APK, original app, account or media behavior was changed. The 80 local tests completed successfully before the signed-DEX scan began; the full signed-DEX scan has not yet reported its final result.

**Next action:** check CI #43739559516 to completion and inspect only `selected_track_path_identity_traces` plus `selected_track_path_missing_method_refs`. Do not start another broad audit. If the run fails, preserve the CI-green `b250aba2` checkpoint and diagnose only the failure. If it succeeds, decide from the exact Track identity events whether either method reaches a player/source/decoder boundary; then update this handoff with the result.

All gates remain false until proven: `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`. Stage A NAV17 remains owner-confirmed PASS; Stage B replacement is NOT CONNECTED / NO-GO. No release APK.

---

# SUPERSEDING CURRENT STATE — 15 Nov 2026, LDT0 Track/Flow split

**Current code checkpoint:** `b250aba2ca5e7555995099683736be572f0ef578`  
**CI:** [#43738914218](https://github.com/manufact-test/nomusic/actions/runs/43738914218) **SUCCESS, 80/80 tests**; exact pinned original verified (16 signed splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-ldt0-track-flow-origin-ci-green-20261115` @ the checkpoint above.  
**Detailed audit:** `docs/android/ANDROID-A1-FLOW-MODE-AND-INTERFACE-CENSUS-20261115.md`.

### Result of the one-callsite follow-up

The only `Ljm4.for(Flow, Scope, Collector)` callsite inside `LDT0.<init>(Album, Track, ...)` is now classified:

- Its Flow argument is the result of `LvF6.case(Album): Flow`. It is Album-derived, not derived from the Track parameter. Close this as a Track-to-Flow candidate.
- The same constructor separately passes its exact Track parameter to `LSW6.if(Track, boolean)`.
- It also passes that Track parameter to `LOW6.<init>(..., Track, ...)`.
- These are exact local Java-reference/register-flow candidates. They do not yet establish player selection, runtime dispatch, decoder input or audio output.

The focused signed-DEX audit remained read-only. CI passed 80/80; no APK, account/media access, runtime hook or vendor behavior change.

### Next exact task — one bounded hop only

Inspect only:
1. `LSW6.if(Track, boolean)`
2. `LOW6.<init>(..., Track, ...)`

Follow the same Track parameter through exact field stores and method calls. Determine whether either path reaches a concrete player-selection/transport owner, source descriptor, or the already identified decoder/audio sink. If neither does, close this branch; do not broaden to generic Flow, MediaSession or decoder APIs.

Do not return to the Album-derived `LDT0 → LvF6.case → Ljm4.for` branch.

**Gates remain:** `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`; CELIKOM replacement remains NOT CONNECTED. NAV17 Stage A remains owner-confirmed PASS; Stage B remains research-only / NO-GO for replacement. No release APK.

---

# SUPERSEDING CURRENT STATE — 15 Nov 2026, Flow mode audit

**Current branch HEAD:** `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`  
**CI:** [#43737913160](https://github.com/manufact-test/nomusic/actions/runs/43737913160) **SUCCESS, 80/80 tests**; exact signed original verified (16 splits / 6 DEX).  
**Exact code backup:** `backup/android-a1-flow-mode-branch-audit-ci-green-20261115` @ `7fc62e8d8469804b66ff58d2f17f6055fc51dd4a`.  
**Detailed result:** `docs/android/ANDROID-A1-FLOW-MODE-AND-INTERFACE-CENSUS-20261115.md`.

The previous handoff's 72/72 / `3f6f9d7` headline is superseded. Current commit changes only the read-only signed-DEX audit and its tests; no runtime hooks or APKs changed.

### What this pass established

- Exact Flow mode switch keys and target blocks are now mapped for the bounded source classes. The selector comes from an integer constructor argument stored in a field; runtime branch choice is **not** proven.
- Direct implementer counts for generic Flow/FlowCollector interfaces are too broad to identify the active player path.
- Of 160 `Ljm4.for(Flow, Scope, Collector)` callsites, exactly one originates in a method accepting both Album and Track: `LDT0.<init>(Album, Track, ...)`. Its Flow argument is not yet proven to derive from that Track.
- `LzE7.collect` has a separate opaque-object-to-Track branch candidate; branch choice and active playback are unproven.
- Existing `LDp0.if` / `Lwp0$a.emit` Track-parameter identity results remain valid, but neither proves active selected playback.

### Exact next task

Inspect only `LDT0.<init>` and its `Ljm4.for` callsite. Prove or reject whether the Flow argument derives from the exact Track parameter. If it does not, close this candidate; do not fan out across the other generic Flow callsites. If it does, follow one bounded hop and distinguish active playback from queue/prefetch/download.

**Gates remain:** `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`; CELIKOM replacement is not connected. NAV17 Stage A remains owner-confirmed PASS; Stage B remains research-only / NO-GO for replacement. No release APK.

---

# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 15 November 2026  
**Repository:** manufact-test/nomusic  
**Current status:** **Stage A = PASS (NAV17 owner verification); Stage B = IN PROGRESS.** Research-only. CELIKOM replacement source is not connected; this is not a release build.

## Current CI-green code and exact next scope — 15 Nov 2026

**Active branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. **Latest CI-green code:** `3f6f9d7ed43e782dc9ab63a72531614e70c6cdb8`. [CI #43734257845](https://github.com/manufact-test/nomusic/actions/runs/43734257845) **SUCCESS 72/72**; original 16 signed splits / 6 DEX, 254,355 methods scanned. **Exact backup:** `backup/android-a1-coroutine-upstream-direct-census-ci-green-20261115`. Read `docs/android/ANDROID-A1-TRACK-COROUTINE-CALLER-IDENTITY-20261115.md` (latest upstream-entry section) before coding.

The exact inbound census found **3 direct upstream references**: `LDp0$a.invokeSuspend -> LDp0.if`, `LDp0.emit -> LDp0.if`, `Lwp0$a$a.invokeSuspend -> Lwp0$a.emit`. These are Flow/coroutine forwarding or resume paths; no direct player-selection identity was established. The **next specific task** is to identify the Flow producer and collector/virtual dispatch into these entry methods and connect it to the **active selected Track**, then join that identity to the previously audited decoder buffer -> audio sink. Do not continue exploring generic coroutine wrappers or claim a player-selection link from method names/types. `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`. **Stage A NAV17 PASS (owner verified); Stage B NO-GO for replacement. No APK, runtime hook or CELIKOM source switched.**

## Prior signed Track / coroutine checkpoint (supersedes renderer-only headline)

Read `docs/android/ANDROID-A1-TRACK-COROUTINE-CALLER-IDENTITY-20261115.md` first. **Last CI-green code** `0de0e4278977f5821ad1de6b0ca879bfa7d110e6`; [CI #43733450288](https://github.com/manufact-test/nomusic/actions/runs/43733450288) **SUCCESS 71/71**, 16 signed splits / 6 DEX, all 254,355 methods covered by caller census. Backup `backup/android-a1-continuation-hierarchy-ci-green-20261115`. Exact direct caller census of `LGp0.new`: `LDp0.if` passes the identical Track argument; `Lwp0$a.emit` passes its Object argument after Track cast; `LFp0.invokeSuspend` passes its `this` continuation with explicit Track=null. The two newly allocated entry continuations `LDp0$a` and `Lwp0$a$a` both inherit `LOe2 -> LZA0 -> Object`. **Do not equate a typed/captured Track with active playback**: `active_selected_item_proven=false`, `same_native_item_to_decoder_proven=false`, resume binding and exact newly allocated constructor capture remain unproven. Continue upstream into selected-item/player identity, then join the previously audited ByteBuffer sink. No new runtime hooks, APK, download, replacement switch or production change. **Stage A NAV17 owner-verified PASS; Stage B research-only, not a release.**

## Latest renderer writer checkpoint (supersedes older research summaries)

Read `docs/android/ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md` before choosing a new hook or rerunning investigations. Signed audit [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS, **49/49 tests**, at `cfd02607829ef854065331571654c94bef5005ba`; exact backup `backup/android-a1-renderer-field-writer-census-ci-green-20261115`. Three typed ByteBuffer fields feed seven exact writer methods. `LcC0.n` / `Lkd6.n` contain `Lad6.final(I)ByteBuffer` → field-write candidates; the same declared fields are read toward virtual audio sink calls. Branches and other writes prevent claiming same runtime object/active selected track. **Stage A NAV17 is owner-confirmed PASS; Stage B has no CELIKOM audio yet.** All selected Track, Album, edition/generation and native decoder linkage gates remain false. No new runtime hook/APK. Ignore historical 'Stage A NO-GO' notes lower in this document: they belong to the pre-NAV17 research epoch.

## Active Git state

- **Only active working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- **Latest CI-green code checkpoint:** `cfd02607829ef854065331571654c94bef5005ba`
- **Latest docs handoff:** current working-branch HEAD; final handoff backup branch is `backup/android-a1-stage-b-audio-sink-audit-final-handoff-20261115`.
- **Static audit CI:** [#43716254136](https://github.com/manufact-test/nomusic/actions/runs/43716254136) SUCCESS; 49/49 tests; exact cross-method renderer ByteBuffer field writers verified as static candidates only.
- **Exact CI-green code backup:** `backup/android-a1-renderer-field-writer-census-ci-green-20261115` @ `cfd02607829ef854065331571654c94bef5005ba` (prior AudioTrack checkpoint `a9dfbbbc` and its backup retained).
- **Pre-fix rollback:** `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`
- **NAV17 owner-known-good baseline:** `backup/android-a1-nav17-owner-real-userinfo-main-music-audible-20261114` @ `d4c0887028b2bfbad7ed59f63ec88a4770f3595d`
- **Last runtime Java hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; unchanged by this static-audit pass.

**Status clarification:** Any older “Stage A = NO-GO” snapshot below refers to a pre-NAV17 checkpoint and is superseded by the owner-verified NAV17 result. Stage A here means the real owner Passport → userinfo → native Yandex Music UI/original playback path. Stage B means CELIKOM replacement source selection and is still incomplete.

## Current Stage B evidence

### Superseding technical checkpoint — 15 Nov 2026 (AudioTrack / ByteBuffer)

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 opened the owner's real Yandex Music account, showed albums and My Wave, and played original Yandex tracks on the handset. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

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


## What is actually done

1. Added read-only Album identity capture at the two signed Track constructors that each have exactly one Album parameter. The hook calls the original constructor once, then associates the resulting Track object with that Album argument by Java reference identity.
2. Added a read-only hook on the exact Track copy method. It calls the original method once, then associates its returned Track object with the Album argument.
3. StageBAudioEvidence carries weak Track/Album references and compares with Java ==. The Track map is bounded to 32 entries; source lineage to 16. Conflicting Track→Album associations revoke the Album link.
4. Album identity can be followed through Track Flow → wrapper → descriptor → factory → DataSource instance → successful open() → positive read(). A read is linked only to the same source and lineage after successful open. Failed reopen and close revoke open proof. Read-path inspection is capped at 256 callbacks per source/reopen window.
5. Static signed-DEX audit and regression tests were extended to report Track/Album constructor and copy-method shapes without making an audio/current-track claim.

## Verified CI — exact scope

- [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**. One Album-typed field on Track; two constructors accept Album but direct same-argument write to Track's own field is **not proven**. One Track+Album→Track copy-method candidate; it reads source Track's Album field, passes the Album argument to a Track constructor and returns a Track. The audit does **not** prove the Album argument is stored on the returned Track. Current selected item is not proven.
- [Clone-only ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations; both Album hooks and all Track/Exo hooks registered. Publisher intentionally absent in this control.
- [Publisher-first ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original publisher 16/16 splits installed, clone co-installed, original remains installed, 25/25 stable observations, no Metrica fatal suppression. Both Album hooks and all Track/Exo hooks registered.
- All three are lab/CI results only. No owner phone was touched. No audio playback or account test was performed. No product APK was published.
- Final publisher-first verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO. stage_a=NO_GO; stage_b_current_player_album_edition_attested=false; audio_or_account_tested=false.



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

## Read these documents first

1. docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md — focused technical handoff.
2. docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md — exact static findings and Album identity observer.
3. docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md — fail-closed Exo source lifecycle.
4. Historical accumulated notes remain in Git history before this documentation cleanup; they are not the current task list.

## Next task — continue, do not restart

The next developer must continue in the existing branch and prove, using signed DEX analysis and read-only identity hooks:

1. Which Track object is the **current selected player item**, distinguishing it from queue, prefetch and download work.
2. Which exact edition/generation object belongs to that selected Track/Album.
3. Whether that same identity reaches the actual decoder input/audio renderer, not merely an Exo DataSource read.

Track Flow and positive DataSource reads are not proof of current audible playback. Do not infer edition semantics from obfuscated names or types. Do not mark Stage A ready until current Track + Album + edition + decoder identity and actual audio are demonstrated.

## Hard constraints

- Do not change the agreed A1 architecture, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend, or original Yandex app/account.
- Keep this work read-only and fail-closed. Every vendor method must execute exactly once and unchanged; no fatal suppression.
- Do not create or deliver a product/release APK from this lab work.
- Do not ask the owner to install anything or perform manual multi-step diagnostics unless a specific owner-side measurement becomes genuinely necessary.
- Work in large coherent blocks. Avoid unnecessary status reports and one-click-at-a-time instructions.
- If the owner sends a diagnostics file, inspect the nine Album counters together with Track/Exo open/read/close counters. Distinguish hook registration, no observations, identity conflict and scan exhaustion.
