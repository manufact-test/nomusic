# CELIKOM Android A1 — checkpoint 20.11.2026: original MediaPeriod before prepare

## Главная цель, запреты

Продолжать **строго** с HEAD единственной ветки `experiment/android-a1-metrica-init-state-observer-arm13-20261112` в `manufact-test/nomusic`. Цель — реальная подмена проверенной альтернативной дорожки в **одном оригинальном проигрывателе** Яндекс.Музыки с безопасным оригиналом на unknown, реальным Pause/Seek/Next/MyWave, не очередная read-only диагностика.

Не переписывать архитектуру; не затрагивать подписанные NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, NAV45 `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`, Android Test.50, Windows, сервер/production и publisher-signed оригинал; не собирать декоративный owner APK без реально проверяемого функционального шага.

## Что именно сделано к передаче

1. Уже подтверждённая ранняя цепь `original Track + Album → creator tCa → Player.e(Sl6,long) source setter` связана с каноническим `NativeReplacementLifecycle`; unknown/Next/nested/throw аннулируют поколение. Поздний `PlaybackInfo.PeriodID + SLOT_B + renderer -4` проверяет тот же original Track/Album/source, но **сам по себе не является точкой до prepare**. Последняя кодовая точка до этой работы: `f2333c947d29fb424ec7ff5452837c294b739446`; [JVM #44702153647 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44702153647), [clone ARM13 #44702153678 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44702153678), [paired ARM13 #44702153622 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44702153622).
2. **Новый исполняемый оригинальный pre-prepare observer:** `d29d85be02482ef44ae7fef90d5e8f70171360f2` добавил строго ограниченный, необязательный хук к original concrete `o96` (MediaPeriod `wh6`), вызываемый **до** `chain.proceed()` метода prepare с callback и long. Через `periodSourceField` он сравнивает Java == оригинального source с последним успешно установленным Player source и исходными `Track+Album`. Никакой смены source/argument, original proceed ровно один раз. Подписанного имени метода из статического скана не экспортируем; обнаружение по единственной проверенной форме. Hook registration и исполняемый playback **не** одно и то же.
3. `ed32310b09527cd26980db47c441d827c31019ad` запретил продвигать неоднозначный original preprepare, если несколько разных MediaPeriod используют один и тот же source в одном поколении (prefetch, повтор); это необратимый fail-closed на данном поколении. [JVM #44704827184 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827184), [предыдущий JVM #44704633989 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704633989); [clone ARM13 #44704827181 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827181), [предыдущий clone #44704633418 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704633418). Paired runs [#44704827138](https://github.com/manufact-test/nomusic/actions/runs/44704827138) и [#44704633500](https://github.com/manufact-test/nomusic/actions/runs/44704633500) оставались **in_progress** при фиксации — обязательно проверить conclusion до утверждения о green.
4. Точечный статический инструмент `android/native-yandex-hooklab/ci/a1_private_original_period_prepare_shape.py` с workflow `.github/workflows/android-a1-track-model-id-edition-annotation.yml`: `a000e0f33ba97fa42c08238d7d4fc8fca2eb3ba3` и последний код `f379dc623fc6e312e307cd5c1c94b7b28d3662fa`. На **издательски подписанном 2025.10.4** проверяет только exact `wh6/o96` форму метода и вложенный callback как интерфейс. [#44705531667 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44705531667), точный итог: `ONE_EXACT_CONCRETE_PERIOD_PREPARE_SHAPE`, `callback_long_void_contract_count=1`, `nested_callback_interface_count=1`, `concrete_override_count=1`. Это **структурная** проверка, не реальное исполнение на телефоне и не контроль текущей воспроизводимой редакции. Исходный XAPK был проверен и удалён в CI, не публиковался.

## Что НЕ готово

`CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Подтверждённый source + предстоящий original prepare **не доказывают** семантический `trackId+albumId+editionId` именно этого source, его уникальное active selection и разрешённый signed CELIKOM grant. Нынешний bridge отключён (original only); ни PCM, ни source byte routing, ни пауза/перемотка с подменой на HONOR 50 не проверены. Подписанного нового APK/ZIP НЕТ.

## Следующий конкретный рабочий шаг

1. Сначала проверить оба paired ARM13 результата `44704827138`, `44704633500`; затем проверить, зарегистрирован ли `ORIGINAL_PERIOD_PREPARE` у owner module, а не только прошёл compile. Не путать тест без музыки с исполнением prepare.
2. В **уже установленном** раннем оригинальном `Track+Album+source+generation` стеке установить **достоверные семантические** `trackId`, `albumId`, `editionId` до prepare и один selected MediaPeriod. Не брать Track String-геттер/Album String-геттер/пустой MediaItem как доказательство: проверка signed-2025 API уже завершилась `CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN`. Не повторять широкий DEX скан и не делать ещё 30 вариантов read-only счётчиков.
3. Как только proven ID+edition, real selected generation, preprepare и signed approved+entitled server grant совпадают, активировать уже существующий `NativeReplacementLifecycle`/`NativePrePrepareAdmission` с однократной original-player source substitution. При любой неоднозначности — ORIGINAL. **Не** включать по одному совпадению source/подписанного метода.
4. Пользователь просит сделать мобильную версию быстрее, работать без промежуточных отчётов; если фактическая подмена ещё не существует, честно отметить это, не выпускать APK только ради статусов.

Порядок чтения: `docs/android/NEXT-CHAT.md` → этот handoff → `docs/android/ANDROID-A1-EARLY-CREATOR-TRACK-ALBUM-ORIGINAL-SOURCE-SETTER-20261120.md` → `docs/android/ANDROID-A1-TRACKID-BRANCH-CFG-ALL-PATH-NO-GO-20261119.md`.

Финальный HEAD ветки см. самый верх `NEXT-CHAT.md` и фактический GitHub ref: этот handoff — docs-only commit поверх `f379dc62`.


## После передачи — 20.11.2026, original prepare seals unknown selection

- Paired ARM13 CI: [44704827138 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827138), [44704633500 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704633500). Это не реальная проверка звучащей альтернативы.
- Runtime bridge теперь при точном original pre-prepare событии вызывает существующий `NativeReplacementLifecycle.atNativePrepare` с неизвестными decoder IDs. Поэтому при наличии enable в будущей интеграции unknown навсегда фиксирует ORIGINAL до `chain.proceed()`; запоздалый exact-looking FileInfo/ID не сможет включить замену посреди трека. По умолчанию весь replacement OFF. Новый JVM fixture временно включает lifecycle **только в тесте**.
- Нет подписанной семантической тройки, approved grant, source-byte routing и работающего APK. Это безопасное закрытие незаконченного runtime handoff, **не подключение звука**. Следующий приоритет — реальные и проверенные ID+edition на этом же original source до prepare и доступ к разрешённому источнику, а не ещё один статический scan.


## 20.11.2026 — unknown prepare fail-closed

Unlinked original `o96.prepare` (wrong/NULL source, lineage mismatch, inaccessible field, nested original setter) now seals the reserved native generation ORIGINAL before publisher `prepare` proceeds. An async semantic ID/grant cannot upgrade it mid-play. New JVM regression verifies wrong-period -> late certification denied -> Next fresh generation; previous matched original-pre-prepare path preserved. Only the existing concrete hook/bridge and model tests changed. No producer IDs, approved audio bytes or actual alternate source yet.


## 20.11.2026 — pre-prepare original DataSource candidate continuity

For exact creator-owned Track/Album/wrapper already linked to original Exo descriptor, factory and a unique unopened DataSource instance, the original `o96.prepare` observer now carries a weak instance identity to `NativeEarlySourceLifecycleBridge`, scoped to exactly the same source generation and concrete original period. Factory rebind, source already opened, different period/Next/Album or original mismatch deny. This bridges a potential byte-source candidate into the existing prepare hook without performing byte routing. Not selected decoder proof, semantic triple, signed grant or audible substitution; default OFF. JVM test verifies positive and all negative cases. No new APK.


## 20.11.2026 — DataSource freshness race correction

`StageBAudioEvidence` now permanently revokes source candidacy upon first `open`/first `read` entry, failure and close, even after a factory gives back the same concrete Java instance. A reused source shared across different track lineages is ambiguous. Bounded weak identity history fails closed if it cannot retain all live references. This affects only candidate evidence, not original audio bytes or publisher method invocation. Java regressions cover open-attempt-before-success, failure/close, same-instance rebind and new source then read. No signed identity triple or audible source routing.


## 20.11.2026 — unique pre-prepare source witness correction

Unlinked concrete original period prepare now irreversibly revokes structural unique-period evidence for this setter generation, even if the expected period arrives later. Reentrant/repeated prepare of same period consumes the previous unopened DataSource candidate, never upgrades it from a later factory result. No audio bytes, source or player control mutation. Tests cover duplicate and foreign-before-later-current conditions; no semantic triple, approved grant or working audio substitution yet.


## 20.11.2026 — final status of previous ARM controls

Latest source code: `41146c6acd9a3b1c2981c95905101cd9a5d8a722` (same branch). JVM [44717158094 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44717158094). Prior 87e4ad3f clone [44716130433 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44716130433), JVM [44716130564 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44716130564). Prior paired [44716130607 FAILURE](https://github.com/manufact-test/nomusic/actions/runs/44716130607) was a clean Android guest two-attempt boot error **before original installed**; it is not a playback verdict. New paired [44717158096](https://github.com/manufact-test/nomusic/actions/runs/44717158096) and clone [44717158107](https://github.com/manufact-test/nomusic/actions/runs/44717158107) still pending when checked. No owner build, identity/grant/alternate byte routing.


## 20.11.2026 — creator-before-Flow Exo source continuity

`StageBAudioEvidence.onNativeTrackWrapperCreated` now captures the verified original creator-owned Track+Album+wrapper at birth scope 12 even if Flow has not emitted the Track yet. Original Exo descriptor/factory/source identity can travel with that weak verified creator lineage. The existing protected NAV40 `classifyNativeTrackAlbumForWrapper` still uses historical 12/16/17 for creator-only births, never converts early creator evidence into an invented Flow match. JVM negative/positive tests added. This does not create a playable replacement or attest semantic ID+edition.


## 20.11.2026 — exact signed API body gate / creator before Flow

[Signed private CI #44718767016 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44718767016) confirms BOTH trackId-annotated FileInfoApi and DownloadInfoApi are abstract interfaces with zero concrete method bodies in the signed 2025 APK. Direct method hooking on these annotated interfaces cannot recover native source-bound ID, so do not repeat that approach. New code commit `ecd039f2edbbfa76c9f5d8b6a27a77aff9930c83` links verified original creator-owned pre-Flow Track/Album/tCa into the existing descriptor/factory/DataSource chain while preserving NAV40 12/16/17 historical categories and original audio. Initial compile-scope failure from `5fd10b57` fixed in `ecd039f2`; JVM #44719300473 SUCCESS; ARM13 #44719300477 and #44719300481 pending at last check. The identity+grant+byte-source blockers are still unresolved.


## 20.11.2026 — concrete original Retrofit trackId candidate reaches source setter

The signed original `FileInfoApi` / `DownloadInfoApi` `@Query/@Path("trackId")` interface methods are abstract (CI #44718767016), so **not directly hookable**. The optional original-process observer now watches `Proxy.newProxyInstance` once and hooks only matching **concrete generated** API methods. It reads a numeric original trackId argument in the existing `Gp0` original Track source scope and returns to vendor via exactly one original `chain.proceed()`. `StageBAudioEvidence` requires that original Track+Album reference and the issuer-created `tCa(String)` numeric constructor key all match before exposing a source-bound candidate. That candidate is carried into the existing `Player.e(Sl6,long)` early setter frame in memory; **no albumId, editionId, approved CELIKOM grant or decoder source URL exists**, and source decision remains original. No IDs or URLs exported. No owner APK released. Failed ARM13 #44723521310/#44723521168 were caused by previous static tests asserting an old one-argument wrapper observation spelling; those tests now require the new actual two-argument original constructor capture without weakening any runtime safety condition. JVM #44723521193 SUCCESS; latest JVM/ARM CI require checking on newer commits.


## 20.11.2026 — real single-player encoded-byte source hook in original Exo

A bounded real HTTPS Range byte stream `NativeExoAlternateByteRoute` was implemented and Java-verified. It accepts only an exact original Exo DataSource reference, a positive native ALT issuance and an already entitlement/rights/TTL/URL-validated CELIKOM grant; it does not create MediaPlayer/AudioTrack, change transport controls or decode PCM. Exact source `open(UC2)` / `read(byte[],int,int)` / `close()` hooks can now delegate to that encoded-byte stream, bypassing the original Exo request only when the alternate is already armed. A failed first open returns to original before any byte; after alternate commits, an error never mixes original bytes. Seek uses the **actual UC2 original DataSpec position**, not elapsed time, UI seek or byte-rate guessing. Read-only pinned-signed UC2 gate verified original long order `for/else/goto` under constructor `(Uri,long,int,byte[],Map,long,long,String,int)`, and exact `toString`/subrange/length readers; runtime reflection only reads `else` as original requested position if strict class/constructor/type checks pass. Fallback: original unchanged.

**Still no live approved native offer, album+edition proven, or runtime audible player confirmation.** Actual byte-stream plumbing exists and is attached to the original Exo method, but `armApproved` has no production caller and replacement remains OFF. Any future owner-enabled admission must occur before the first Exo `open()` and must never grant a different selection or prefetch object.


## 20.11.2026 — source bytes actually wired through the original Exo methods

Latest executable code `745179b11b0f837d1cdf9d46cbe142f225c2ffe3`: original signed `RetryingBalancingDataSource.if(UC2)`, `read([BII)I`, `close()V` intercepted with an **approved-only** HTTPS Range encoded stream `NativeExoAlternateByteRoute`; all other calls do exactly one real vendor method as before. One native ExoPlayer, no parallel MediaPlayer/PCM interception. Strictly exact original `UC2.else:J` signed byte-position field verified from constructor `(Uri,J,I,[B,Map,J,J,String,I)`, `toString`, `case(JJ)`, `try(J)`; private CI 44728951933 SUCCESS. Strict original Track+Album+DataSource + full source-bound FileInfo triple + NativeGrantContract signed approved entitlement + issuer original MediaPeriod preprepare now connect through canonical `NativeEarlySourceLifecycleBridge` to same stream router. Synthetically tested authorized alt bytes, seek, Next cancellation, wrong source fallback, signed grant denial. JVM #44730902321 SUCCESS. Production grant callback, owner activation and independently verified original albumId/editionId remain **absent**, so actual phone always runs original; no owner APK or audible substitution. Original API annotation labels for FileInfo and DownloadInfo contain only trackId, CI 44729237330 SUCCESS. ARM13 code runs may still be pending. Never infer PASS from the synthetic stream tests.
