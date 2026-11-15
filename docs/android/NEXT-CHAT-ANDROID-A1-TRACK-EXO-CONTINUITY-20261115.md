> **CELIKOM Android A1 — TRACK/ALBUM IDENTITY + EXO SOURCE CONTINUITY — 15.11.2026**
>
> **Рабочая ветка:** experiment/android-a1-metrica-init-state-observer-arm13-20261112
>
> **Последний кодовый checkpoint:** a655712d210189f3bc611847235de3ed4d985c1a (read-only Track Album constructor/copy hooks).
>
> **Последний branch HEAD до обновления этих документов:** 90f8ea394e1ac4168aa63f976e17fd18eb24befb (тот же код + signed DEX static-flow audit/tests).
>
> **CI SUCCESS:**
> - [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): exact Track+Album copy-method shape, Album-argument-to-Track-constructor candidate path.
> - [Clone-only ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **25/25**, both Album hooks and all Track/Exo hooks REGISTERED.
> - [Publisher-first ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original 16/16 splits and clone co-installed, **25/25**, no suppression.
>
> **Важно:** verdict METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO; Stage A = **NO-GO**. Current selected Track/Album/edition and decoder are NOT attested; no audio/account playback test was performed. Constructor's direct Album field assignment is not statically proven; see the detailed Album identity document.
>
> **Точный резерв текущего read-only checkpoint:** backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb.
>
> **Резерв до большого захода:** backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5.
>
> Сначала прочитать:
> 1. docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md
> 2. docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md
> 3. docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md
>
> **Следующая задача:** доказать identity именно текущего выбранного Track (не prefetch/queue), его edition/generation и связь того же объекта с фактическим decoder input/audio renderer. Не считать Track Flow или DataSource.read доказательством текущего звучащего трека. Не менять архитектуру, Test.50, frozen A1, Windows, extension, backend или оригинальное приложение. Работать read-only; не просить владельца устанавливать APK или выполнять ручные действия, пока это действительно не потребуется.

---


> **REVISED FAIL-CLOSED REGRESSION CHECKPOINT, 15.11.2026:** `9af55e5909592021f75b69d7b4d1b5cec2252cfc` (только Java regression; исполняемый код по-прежнему `2dc2e1f0`). Исправлено слабое место тестов: теперь отдельные свежие linked-source сценарии требуют `TRACK_SOURCE_READ_LINK=NONE` после `close()`, позднего `open()` failure и source rebind; лишь новый успешный open разрешает `ONE`. Проверить [clone-only CI #43700267919](https://github.com/manufact-test/nomusic/actions/runs/43700267919); publisher-first для **того же исполняемого кода** [#43699883681](https://github.com/manufact-test/nomusic/actions/runs/43699883681), clone-only [#43699883677](https://github.com/manufact-test/nomusic/actions/runs/43699883677). Stage A **NO-GO**, source-binding ≠ current audible track. Актуальная подробная запись в [source lifecycle документе](ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md).

---

> **SOURCE-OPEN FAIL-CLOSED FOLLOW-UP — 15.11.2026.** Последний код `2dc2e1f0ad394f83bed27e2e2d272179e85441cd`, резерв до этого малого исправления `backup/android-a1-source-open-close-pre-failure-reset-20261115` @ `975ec09e`. На случай позднего/перекрывшегося исключения vendor `open()` добавлен отдельный `onExoSourceInstanceOpenFailure`, который отменяет любое старое `sourceOpened` (без подмены исходного исключения). Новые [clone-only CI #43699883677](https://github.com/manufact-test/nomusic/actions/runs/43699883677) и [publisher-first CI #43699883681](https://github.com/manufact-test/nomusic/actions/runs/43699883681): **проверить конечный статус**. Предыдущий `9a22ec1e` green не переносить на этот код. **Stage A NO-GO, audio/current Track/decoder не проверено.**

---

> **НОВЫЙ ANDROID A1 CHECKPOINT 15.11.2026 — DataSource lifecycle (read-only).** [Открытие→чтение→закрытие](ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md): код `9a22ec1e0b0fbd58bcf39e63fe61386514924681`, резерв `backup/android-a1-source-read-after-open-pre-guard-20261115` @ `55d2f554`. Убрали ложное доказательство `read()` без успешного `open()`, добавили дедуп уникальных source объектов, revoke на failed reopen/close, конечный бюджет сканирования в read hot path. Signed exact `close()V` подтверждён [#43698830014](https://github.com/manufact-test/nomusic/actions/runs/43698830014) SUCCESS. **Проверить** итог новых [clone-only CI #43699251424](https://github.com/manufact-test/nomusic/actions/runs/43699251424) и [publisher-first CI #43699251417](https://github.com/manufact-test/nomusic/actions/runs/43699251417); предыдущий green к новому коду не относится. **Stage A NO-GO, audio не проверено.** Остальные передачи ниже исторические.

---

> **ПОСЛЕДНИЙ ANDROID A1 CHECKPOINT — 15.11.2026, два coroutine resume.** [Точный RAa handoff](ANDROID-A1-RAA-SOURCE-RESUME-IDENTITY-20261115.md), код `2267c64f1df04b31a47f1a6e9d67b367ceea56db`, резерв `backup/android-a1-raa-source-resume-pre-identity-20261115` @ `df872b6d`. Signed static [#43696198020](https://github.com/manufact-test/nomusic/actions/runs/43696198020) SUCCESS: `RAa.invokeSuspend` повторно вызывает download2.o.for с той же continuation и **null wrapper**. Ранее подписанный DEX доказал `Fp0.invokeSuspend → Gp0.new` с null Track. Теперь оба перехода наблюдаются только по bounded weak `==` identity, с отдельными counters и fail closed. Оба Fp0/RAa hooks **REGISTERED**, все шесть hooks видны в ограниченной диагностике; [clone-only #43696449267](https://github.com/manufact-test/nomusic/actions/runs/43696449267) SUCCESS 25/25 и [publisher-first #43696449282](https://github.com/manufact-test/nomusic/actions/runs/43696449282) SUCCESS/NOT_AUDIO (original 16 splits + clone co-install). Точный принятый CI-green резерв `backup/android-a1-fp0-raa-dual-resume-ci-green-20261115` @ `2267c64f`. **Stage A NO-GO, никаких release/audio/substitution утверждений.** Исторические передачи ниже.

---

> **ТЕКУЩАЯ ANDROID A1 ПЕРЕДАЧА — 15.11.2026, coroutine Fp0.** [Новый точный разбор](ANDROID-A1-FP0-COROUTINE-RESUME-IDENTITY-20261115.md): в подписанном DEX `Fp0.invokeSuspend` действительно возобновляет `Gp0.new` с **тем же continuation** и с **null вместо Track аргумента** (static [#43695462019](https://github.com/manufact-test/nomusic/actions/runs/43695462019) SUCCESS). Read-only код `6e409f9920c8ea0d47bf08d37d9da827bee89b2a` связывает continuation с исходным Flow-Track только по weak reference `==`, fail-closed. Clone-only [#43694941351](https://github.com/manufact-test/nomusic/actions/runs/43694941351) SUCCESS 25/25, publisher-first [#43694941316](https://github.com/manufact-test/nomusic/actions/runs/43694941316) SUCCESS NOT_AUDIO; parser пятого hook обновлён в `495d37e3`, новые CI #43695595723/#43695595735 ещё проверяются. **Stage A NO-GO: реальной подмены и identity аудиопотока нет.** Рабочая ветка та же, резерв до кода `backup/android-a1-track-continuation-pre-identity-20261115`. Все прежние handoff ниже исторические.

---

> **Актуальное дополнение — 15.11.2026.** Сохранён следующий кодовый checkpoint `f7983590bee3eec38ee8b09fd41859b64192f2df`; резерв до hardening: `backup/android-a1-track-exo-identity-pre-hardening-20261115` @ `746abe055b4bf903e3d280834e7cf432a0b1bd96`. [Подробности, новые raw счётчики и coroutine-ограничение](ANDROID-A1-TRACK-EXO-IDENTITY-HARDENING-20261115.md). Clone-only [#43654168986](https://github.com/manufact-test/nomusic/actions/runs/43654168986) **SUCCESS**, 25/25, Java tests green. **Это не доказательство аудио и не готовая CELIKOM-подмена; Stage A NO-GO**. Publisher-first [#43654169076](https://github.com/manufact-test/nomusic/actions/runs/43654169076) **SUCCESS**, original 16 splits + clone co-install, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, Stage A NO-GO (нет audio/login/current track binding). Старый `d8049537` ниже — предыдущий, а не текущий код.

# CELIKOM Android A1 — Track → Exo continuity handoff, 15.11.2026

**Приоритет:** эта передача актуальнее накопительной истории в `NEXT-CHAT.md`. Не начинать с нуля и не менять продуктовую архитектуру.

## Репозиторий

- Repo: `manufact-test/nomusic`
- Active research branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- Code checkpoint: `d80495370ff8f442b6993c688783c24547caa24f`
- Exact backup: `backup/android-a1-track-exo-continuity-pre-ci-20261115` @ `d80495370ff8f442b6993c688783c24547caa24f`
- Read-only signed DEX audit: [#43648001634](https://github.com/manufact-test/nomusic/actions/runs/43648001634) — SUCCESS; static candidates only, not playback proof.
- Latest clone-only ARM13 run: [#43649573590](https://github.com/manufact-test/nomusic/actions/runs/43649573590), commit `d8049537` — **SUCCESS**. Java regression tests, scoped-module build, private XAPK verification, DEX classifier, fresh Android 13 ARM guest and no-suppression 75-second standalone clone stage all passed. Clone lifecycle was stable **25/25**. This is strictly `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`: publisher original was intentionally absent, no account or audio was tested, owner phone was untouched, Stage A remains **NO-GO**. The four new Track/source hooks all reported `REGISTERED`, but this only proves hook installation; no runtime Track→Exo identity counters or current album/edition proof were produced. Do not call this a CELIKOM audio pass.
- Older failures #43648828954 and #43649323267 were caused by stale test expectations. Fixes are in `d80495370ff8f442b6993c688783c24547caa24f`; do not report those older failures as the current run result.

## Static findings

Signed DEX audit found this candidate path:

1. `LDp0.emit(Object, Continuation)` forwards a Track object into `LDp0.if(ru.yandex.music.data.audio.o, Continuation)`.
2. `LDp0.if` calls `LGp0.new(LGp0, ru.yandex.music.data.audio.o, Oe2)`.
3. `LGp0.new` reads Track's String field `default`, then calls `LtCa(String)`; it then calls `Lou3.new(LtCa, Fp0)`. This is a static same-method instruction sequence, not yet a branch-sensitive runtime proof.
4. `com.yandex.music.shared.player.download2.o.for(o, qX8$d, LtCa, f6a, n26, Oe2)` calls the native descriptor builder `o.while(...)`.

This is a candidate native Track → wrapper → descriptor path. It does **not** prove current audible track, edition/generation, decoder selection or CELIKOM substitution. A FileInfo `trackId` parameter or download-info endpoint alone is not proof of current playback binding.

## Code changes in checkpoint

Read-only hooks were added to `ExitCallsiteWitness.java`, scoped only to `pro.celikom.yandex.nativeclonelab`:

- `Dp0.emit` — native Track flow emission.
- `Gp0.new` — selected Track enters wrapper creation.
- `tCa(String)` constructor — wrapper linked to active Track scope.
- `download2.o.for(..., tCa, ...)` — wrapper enters the main source builder.
- Weak-identity links: Track → wrapper → descriptor → factory result → Exo source instance → open/read.

**Important fix:** Java `Class.forName` requires binary names without DEX's `L...;` wrapper. Correct names are `Dp0`, `Gp0`, `tCa`; previous `LDp0`, `LGp0`, `LtCa` were wrong. Fixed in checkpoint `d80495370ff8f442b6993c688783c24547caa24f`.

`StageBAudioEvidence.java` stores only bounded counters and weak references, compares objects with `==`, and does not read Track fields, URLs, headers, account data, tokens or audio. Vendor methods continue once via `chain.proceed()`; no source replacement is applied. The Java harness tests the full identity chain and mismatched-object fail-closed cases.

Key files:
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/StageBAudioEvidence.java`
- `android/native-yandex-hooklab/ci/test_a1_stage_b_audio_evidence.py`
- `android/native-yandex-hooklab/audit_native_selected_item_handoff.py`
- `android/native-yandex-hooklab/audit_native_track_identity_static.py`

## Not proven — do not overclaim

- Runtime registration of all new hooks.
- Continuous runtime identity from the current Track Flow to the Exo source read.
- Current track ID + edition + generation, audible selection or decoder-before-prepare.
- CELIKOM audio replacement. Export intentionally remains `AUDIO_STAGE_B_STATUS / CELIKOM_REPLACEMENT / NOT_CONNECTED`.
- The separate `audit_native_track_identity_static.py` has not been confirmed as executed; require a concrete CI run and verdict before citing it.

## Next work

1. Run [#43649573590](https://github.com/manufact-test/nomusic/actions/runs/43649573590) is complete and green; do not rerun it without a source change.
2. On the next owner diagnostic, check registration events `AUDIO_NATIVE_TRACK_FLOW_HOOK`, `AUDIO_NATIVE_TRACK_REQUEST_HOOK`, `AUDIO_NATIVE_TRACK_WRAPPER_HOOK`, `AUDIO_NATIVE_MAIN_SOURCE_HOOK`.
3. Check counters `FLOW_TRACK_SAME_OBJECT`, `TRACK_WRAPPER_LINK`, `WRAPPER_DESCRIPTOR_LINK`, `TRACK_DESCRIPTOR_FACTORY_LINK`, `TRACK_FACTORY_SOURCE_LINK`, `TRACK_SOURCE_OPEN_LINK`, `TRACK_SOURCE_READ_LINK`. Localize a broken hop; do not expand blind hook sweeps.
4. If no diagnostic is supplied yet, continue source/CI analysis autonomously and wait for the owner to send it.

## Owner constraints

This is a laboratory research branch, not a release branch. Do not distribute or request installation of an observer APK. Do not disable Play Protect, disturb the original Yandex install, change Test.50/frozen A1, Windows, extension, backend/API/DB or production. Keep the one native Yandex player architecture. Work in large blocks; avoid step-by-step manual chores and unnecessary reports.


## Первое сообщение следующему чату

Скопировать целиком:

> Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай существующую работу, ничего не начинай с нуля и не меняй согласованную архитектуру.
>
> **GitHub:** `manufact-test/nomusic`
>
> **Единственная активная исследовательская ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
>
> **Кодовый checkpoint:** `d80495370ff8f442b6993c688783c24547caa24f`
>
> **Точный резерв кода:** `backup/android-a1-track-exo-continuity-pre-ci-20261115`
>
> Сначала прочитай `docs/android/NEXT-CHAT.md` и `docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md`.
>
> CI [#43649573590](https://github.com/manufact-test/nomusic/actions/runs/43649573590) завершился SUCCESS: no-suppression clone-only Android 13 75s, 25/25 стабильных наблюдений; все четыре Track/source hooks зарегистрировались. Но original publisher был намеренно отсутствовал, аудио и аккаунт не тестировались, поэтому это НЕ product pass, Stage A остаётся NO-GO.
>
> Текущая задача — read-only runtime identity witness native Track Flow → `Gp0.new` → `tCa` → основной Yandex Exo descriptor/source path. Статическая цепочка найдена, runtime identity и реальная подмена ещё НЕ доказаны. В следующей диагностике проверь registration events и counters полной цепочки. В статусе `AUDIO_STAGE_B_STATUS` пока честно остаётся `CELIKOM_REPLACEMENT / NOT_CONNECTED`.
>
> Не выдавай лабораторный APK за рабочую версию и не проси владельца ничего устанавливать. Не трогай Test.50, frozen A1, Windows, extension или backend. Если владелец пришлёт диагностику — сначала разбери её, не заставляй его выполнять лишние ручные шаги. Работай крупными блоками и продолжай самостоятельно.
