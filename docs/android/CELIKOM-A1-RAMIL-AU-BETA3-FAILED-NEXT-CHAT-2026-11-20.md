## BETA5 — signed owner diagnostic APK ready (20.11.2026)

**Artifact:** `CELIKOM-A1-RAMIL-AU-BETA5-HONOR50-20261120.zip` in the owner's Library at `/CELIKOM-A1-RAMIL-AU-BETA5-HONOR50-20261120.zip`. ZIP contains the 71,569,388-byte APK and Russian phone instructions. APK SHA256: `3c070a7b5b72482fb271c6e263504354bfbfced6f87949de3f0a3483468eb7b2`.

**Build and verification:** source commit `54452d21ae91a5c4c81b4b8ccf0f8d55e3fb17a8`; [signed owner diagnostic workflow #44774533273 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44774533273); artifact ID `14649922260`. The exact owner signer certificate `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` was verified and matches the installed owner certificate. CI used `UPDATE_EXISTING`, did not authorize a fresh install, and did not touch the owner's physical phone. The native Android 13 ARM publisher-first/clone-second 75-second smoke test passed and cleanup completed.

**Do not overstate the result:** machine verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `stage_a=NO_GO`, `audio_or_account_tested=false`, `diagnostic_only_not_product_or_releasable=true`. The emulator did not sign into CELIKOM or play audio. This is specifically the next HONOR 50 owner diagnostic/audio trial, not proof that replacement works.

**BETA5 UI correction:** one top-right `CELIKOM: <status> · TXT` control is restored; separate BETA/join control and speculative Yandex-settings entry are absent. CELIKOM auto-starts from the saved CELIKOM session. Status values distinguish checking, enabled, no session, no access, server failure and error. Pressing the same control exports the privacy-safe TXT.

**Owner test:** install the ZIP's APK as an update over BETA4. Do not uninstall the clone, clear its data, or remove the original Yandex Music app. Launch the clone and check that the single top-right status/diagnostic control is visible and reports `ВКЛ`. Then play Ramil' «Ау», ID `144530503`, at `00:43–00:54`. Decide by ear whether the alternate version plays. If the status is not `ВКЛ`, the button is missing, or the censored original plays, press the diagnostic button if available and send the TXT. Do not test Pause/Seek/Next/MyWave yet.

# CELIKOM Android A1 — BETA3 failure / BETA5 current handoff (20 ноября 2026)

## BETA4 update — signed owner-phone diagnostic build (20.11.2026)

**Source commit:** `67db1226d98b6c2d0666f064c6441409e17d5d63` on the same single branch. This is a one-time diagnostic trial build, not a product release.

### What changed after BETA3

- Runtime now hooks the exact `Fp0.invokeSuspend(Object)` and restores the linked original Track only during that continuation resume.
- Runtime now hooks the exact `RAa.invokeSuspend(Object)` and restores the linked original `tCa` wrapper only during that continuation resume.
- The Retrofit `Proxy.newProxyInstance` witness is installed before `attachBaseContext`; the exact FileInfoApi/DownloadInfoApi proxy handler is then hooked for the annotated `trackId` method.
- New privacy-safe counters distinguish proxy-hook registration, proxy creation, annotated method selection, handler invocation, a missing Track scope, and the subsequent issuer/creator/source/audio stages. No raw track ID, token, URL, account or audio bytes are exported.
- The approved one-track Ramil' «Ау» ID `144530503` remains explicitly allowlisted beside the two earlier trial IDs. No other IDs are admitted.
- Removed the floating BETA and diagnostic controls. A single CELIKOM entry is attempted inside Yandex settings; the saved CELIKOM refresh session is automatically revalidated on app launch. If no CELIKOM session exists, the only manual login is to CELIKOM, never to Yandex. This UX still needs the owner's phone confirmation.

### CI and APK facts — do not overstate

- JVM/native observer regressions: [#44769299260 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44769299260).
- Full signed Android 13 ARM owner-phone build: [#44769299230 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44769299230).
- Clone-alone differential: [#44769299113 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44769299113).
- The 75-second emulator run installed and launched the original publisher first and the CELIKOM clone second; all targeted hooks registered, the clone remained stable, and there were no observed uncaught exceptions.
- **The emulator did not log into an owner account or play music.** The machine verdict is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `stage_a=NO_GO`, `audio_or_account_tested=false`, `diagnostic_only_not_product_or_releasable=true`. This confirms hook registration and launch stability only; it does not prove proxy invocation, publisher track ID capture, Exo source binding, or audible replacement.
- APK: `CELIKOM-A1-RAMIL-AU-BETA4-HONOR50-20261120.apk`, 71,569,388 bytes, SHA256 `05d078075edbe88d028dbb8b70f5e2b3cddd128cdadd250885e838f6b660dedc`. Persistent CELIKOM owner signer verified; SHA256 certificate `048D76E1C4447FA4F3AC976C45D5A0F8427C087FA665C4FCA88CE5CAA068F9BF`, matching the previously installed owner signer. APK ZIP integrity checked; embedded original publisher APK and CELIKOM observer module are present; module DEX contains the new resume/proxy hooks and auto-start/settings entry.
- GitHub artifact `14647192187`; APK was copied to the owner's Library at `/CELIKOM-A1-RAMIL-AU-BETA4-HONOR50-20261120.apk`.

### Next action — owner phone, not another static research loop

1. Install BETA4 **as an update over the existing BETA3 clone**. Do not uninstall, clear data, or remove the original Yandex app; the existing CELIKOM session must remain available.
2. Launch the clone and check that it attempts automatic CELIKOM activation. There must be no floating BETA/diagnostic buttons.
3. Open Yandex settings and check for the single `CELIKOM A1` entry. If it is absent, report that fact; do not sign into Yandex again.
4. Play 10AGE / Ramil' «Ау», publisher track ID `144530503`, only at `00:43–00:54`. First decide whether the alternate audio is actually audible. Do not test Pause/Seek/Next/MyWave until it is.
5. If the censored original still plays, use `CELIKOM A1 → Сохранить диагностику` and send one TXT. Inspect first: `ISSUER_PROXY_HOOK_REGISTERED`, `ISSUER_PROXY_CREATED`, `ISSUER_METHOD_SELECTED`, `ISSUER_HANDLER_INVOKE`, `ISSUER_TRACK_SCOPE_MISSING`, `ISSUER_TRACKID`, then `EXACT_BETA_CREATOR`, `ORIGINAL_SETTER`, `SIGNED_MPEG_READY`, `GRANT_ADMITTED`, `EXACT_PREPARE`, `DATASOURCE_ARMED`, `AUDIO_OPEN`, `AUDIO_READ`.

**Do not call BETA4 a working replacement.** The only proof of success remains audible alternative bytes in the original Yandex ExoPlayer on HONOR 50. If the next phone diagnostic still has `ISSUER_TRACKID=NONE`, continue at the exact Retrofit proxy lifecycle; if issuer is present but source counters remain NONE, continue at the original `Track → tCa → native source → Exo DataSource` chain. No AppMetrica/DEX detour, no architecture reset, and no changes to Test.50/NAV40/NAV45/Windows/backend.


## Фиксированная точка

- Repo: `manufact-test/nomusic`
- Только ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- HEAD до этой передачи: `1566bdc8f959cce95b9afd3968872a1bd7ba5823`; HEAD самой документации смотреть в GitHub.
- Последняя проверенная владельцем APK: `CELIKOM-A1-RAMIL-AU-BETA3-HONOR50-20261120.apk`, исходный CI [#44753682381](https://github.com/manufact-test/nomusic/actions/runs/44753682381) SUCCESS. **Живой акустический результат: FAIL, всегда звучит цензурный оригинал.** Это не релиз, не подтверждённое воспроизведение альтернативы.
- Новый TXT с HONOR 50 / Android 13: `CELIKOM-A1-Diagnostics-1795187145828.txt` (приложен пользователем к чату 20.11.2026, не выкладывать в публичный репозиторий). Тест: 10AGE / Ramil' — «Ау», предполагаемый publisher trackId `144530503`; тестовый участок ~00:43–00:54. Нельзя считать publisher ID **доказанным для конкретного запуска**, потому что issuer callback не сработал.
- Оригинальные Yandex app, Windows, Test.50, NAV40/NAV45 и backend не менять. Один ExoPlayer Яндекса, не делать второй плеер/второй вход в Яндекс.

## Реальная диагностика — не интерпретировать в пользу успеха

Новый маркер `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA_RAMIL_AU_20261120` **ACTIVE** — верная версия BETA3. Старый `DIAGNOSTIC_BUILD=NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY` остаётся как baseline. Статический `CELIKOM_REPLACEMENT=NOT_CONNECTED` — legacy strict triple status, не заменяет актуальных beta counters.

**Актуальные beta counters:**

| Этап | Из TXT | Смысл |
| --- | --- | --- |
| `OWNER_ENABLED` | `ONE` | Владелец вошёл в отдельный CELIKOM и нажал BETA, доступ подтверждён |
| `ISSUER_TRACKID` | `NONE` | Нет события exact original Retrofit trackId по разрешённому ID |
| `EXACT_BETA_CREATOR` | `NONE` | Нет связки original publisher Track ↔ tCa wrapper и issuer ID |
| `ORIGINAL_SETTER` | `NONE` | Не привязана успешная смена original Player source к разрешённому треку |
| `PREFETCH_STARTED`, `SIGNED_MPEG_READY` | `NONE`, `NONE` | Не было prefetch альтернативы |
| `OWNER_RESOLVE_REQUEST`, `GRANT_ADMITTED` | `NONE`, `NONE` | CELIKOM resolve/grant вообще не запрашивался для источника |
| `EXACT_PREPARE` | `FEW` | Реальный original MediaPeriod.prepare засвидетельствован |
| `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN`, `AUDIO_READ` | всё `NONE` | В ExoPlayer ни разу не использовались альтернативные байты |

**Коррелирующие Stage B:** `FILEINFO_DTO=FEW`; `EXO_DESCRIPTOR_BUILT=FEW`; `EXO_FACTORY_CREATED=FEW`; `EXO_SOURCE_INSTANCE=MANY`; `EXO_OPEN_OK=MANY`; `EXO_READ_POSITIVE=MANY`; `EXO_IO_FAILURE=NONE` — оригинальное аудио работает. `NATIVE_TRACK_FLOW_EMIT=ONE`; `NATIVE_TRACK_SOURCE_REQUEST=ONE`; `TRACK_WRAPPER_LINK=ONE`; `TCA_CREATOR_OWNER_ENTER=FEW`; `TCA_CREATOR_WRAPPER_CONSTRUCTED=FEW`; однако `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, `WRAPPER_DESCRIPTOR_LINK=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`, `TRACK_FACTORY_SOURCE_LINK=NONE`. Механизм не связал оригинальный source и реально читаемый Exo DataSource, несмотря на реальное чтение оригинального звука.

В TXT есть `LOG_TRIMMED`; прошлые строковые события регистрации могли быть обрезаны. Вышеперечисленные экспортные счетчики снимаются из памяти по нажатию «Диагностика», поэтому для этих категорий `NONE` достоверен в рамках наблюдаемого процесса. `METRICA_EXCEPTION_SUMMARY=MANY`, но это **не доказывает**, что именно AppMetrica блокирует аудио; не уводить работу туда.

## Приоритетный пул задач — выполнять по порядку

**P0 — первый ненулевой issuer ID, без фальшивой личности.** На живом clone `ISSUER_TRACKID=NONE`, поэтому открыть `ExitCallsiteWitness.installPublisherTrackIdProxyWitness()` / `hookConcretePublisherTrackIdProxy()` и `StageBAudioEvidence.onPublisherAnnotatedTrackId()`. Проверить, когда реально создаётся Retrofit proxy, что конкретный `InvocationHandler.invoke` вызывается на active track и что выбран `@Query("trackId")`. Возможен промах: proxy создан до установки hook или использован cached request, обрезан контекст вызова, неверный allowed trackId, нерелевантный путь FileInfoApi. Не объявлять какую-либо гипотезу доказанной. При необходимости добавить **только обезличенные и ограниченные по частоте** события: REGISTERED/PROXY_SEEN/ISSUER_ID_PRESENT/ALLOWLIST_MATCH/Gp0_SCOPE_MATCH; без самого trackId/токенов/URI/аккаунта в экспорте. Проверить фактическое соответствие проигранного «Ау» publisher ID `144530503`; не угадывать.

**P1 — вторая недостающая source chain, не распространять publisher bytes по наитию.** Разобраться с `NATIVE_MAIN_SOURCE_ENTER=NONE` и `WRAPPER_DESCRIPTOR_LINK=NONE`. Код: `ExitCallsiteWitness.installNativeTrackSourceContinuityWitness()` (оригинальная `download2.o.for(... tCa ...)`) и `installExactNativeExoSourceWitness()` (descriptor→factory→DataSource), `StageBAudioEvidence.enterNativeMainSourceRequest()` / `onNativeExoDescriptorBuiltForCurrentWrapper()`; проверить регистрацию методов и реальный runtime путь. Может быть другой coroutine callsite либо нужная установка до жизненного цикла. Требовать exact Java object reference, successful original Player setter/generation, untouched/unopened Exo DataSource. Нет данных — продолжать original audio.

**P2 — при появлении P0+P1 использовать существующую signed owner beta, без второго плеера.** `NativeOwnerControlPlane.warmFromPublisherTrackId()` → `requestForTrackIdBeta()` → `NativeEarlySourceLifecycleBridge` → `NativeExoAlternateByteRoute`. Существующие условия approved+entitled, signed HTTPS, MIME MPEG, Range/206, bounded original pre-prepare, generation invalidation и Next/Stop сохранять. Не сканировать снова все DEX, не переключаться на PCM/Metrica без ясного нового факта. Факт успеха только `AUDIO_READ` не `NONE` + **слышно альтернативу владельцу**.

**P3 — нормальный UX; пользователь прямо отверг отдельную BETA-кнопку, отдельную форму и плавающую диагностику.** Яндекс-логин внутри клона уже есть, но backend CELIKOM использует **отдельную** серверную сессию, email/password и `auth/activate`. Они не являются автоматически общей учёткой. Сейчас `NativeOwnerControlPlane.hasSession()` читает Android Keystore encrypted refresh token; `start()` проверяет entitlement. Реализовать после исправления P0/P1 тихий автоматический `start()` при уже существующей сессии CELIKOM, а не требовать нажимать BETA при каждом процессе; первоначальная авторизация CELIKOM всё ещё нужна только если нет законной связанной сессии. Перенести первоначальный CELIKOM login в штатный экран CELIKOM (или добавить законное account-linking позже), а не выдавать Yandex пароль за CELIKOM credential. Скрыть плавающие `CELIKOM BETA` и `Диагностика NAV9` из пользовательского музыкального экрана; экспорт диагностики оставить только в настройках/режиме разработчика. Не убирать серверные права доступа и контроль одобрения.

**P4 — один повторный акустический тест после доказанного движения P0/P1.** Тот же 10AGE/Ramil' «Ау», publisher ID `144530503`, 00:43–00:54. Один signed APK/Library для HONOR 50 Android 13, не выдавать серию неизменённых APK. Сначала слышим оригинал vs альтернативу; затем Pause, Seek, Next и MyWave. TXT только если нужно. CI/JVM PASS — **не** звуковой PASS.

## Правила продолжения

1. **Не начинать архитектуру заново.** Не перебирать legacy NAV40/NAV45, Test.50, Windows, backend; этот проход нужен для первого звучащего alternative inside original Yandex ExoPlayer.
2. Два рабочих препятствия подтверждены пользователем и диагностиками: отсутствующий issuer ID в beta и отсутствующий native main-source → Exo chain. Остальное после них.
3. Длинные блоки реальной работы без промежуточных микрорепортов. Проверки через GitHub CI. Изменения атомарно в этой же ветке. Успех звука не объявлять без теста владельца.
4. До выпуска новой версии проверить, что появился реальный маршрут от издательского Track/ID до оригинального DataSource. Не выпускать ради зеленого CI или косметики.
5. Документировать законченные этапы в этом файле и `CELIKOM-A1-LIVE-AUDIO-NEXT-CHAT-2026-11-20.md`, передать новый HEAD следующему чату.


## Code-level fix after the failed BETA3 run (20.11.2026)

The first missing links were traced to a concrete lifecycle gap in the clone hook wiring: Stage B already retained exact Fp0 (Track request) and RAa (main source) continuation-to-object links, and its regression model already tested recovery on coroutine resume, but the runtime module hooked only their constructors and the initial suspend methods. It never restored the Track/wrapper ThreadLocal scopes around the generated invokeSuspend(Object) callbacks. Once the original suspend method returned, the ThreadLocal scope was popped; a later Retrofit issuer call or descriptor construction on coroutine resume could therefore arrive without the exact Track/wrapper context.

The fix now:
- hooks the exact signed Fp0.invokeSuspend(Object) and restores only its previously linked original Track for the duration of that resume;
- hooks the exact signed RAa.invokeSuspend(Object) and restores only its previously linked original tCa wrapper for that resume;
- installs the Retrofit Proxy.newProxyInstance witness before Application.attach enters attachBaseContext, so a FileInfoApi/DownloadInfoApi proxy created during app attachment is not missed;
- retries the proxy-hook registration after attach if an early class lookup or hook registration failed;
- exports privacy-safe counters for proxy hook registration, exact API proxy creation, annotated method selection, handler invocation, and an allowlisted ID that arrived without a restored Track scope.

No publisher ID, token, account, signed URL or audio data is exported. The original publisher methods still execute exactly once. All unlinked, conflicting or stale continuations remain fail-closed. This is a targeted wiring fix inside the existing architecture, not a new player or an alternate authorization path.

**Historical validation note (superseded):** at the time this section was first written, Java/Python and ARM13 CI were pending. The BETA4 results and owner-phone test requirement are recorded at the top of this document.


## BETA5 owner-phone diagnostic result — 20.11.2026

**Owner result:** BETA5 was tested on HONOR 50 / Android 13 with Ramil' «Ау», publisher track ID `144530503`, at the requested section. The owner reports that the replacement still does not work / alternate audio is not heard. **BETA5 is a failed audio trial, not a working build or release.**

**Exact diagnostic:** `CELIKOM-A1-Diagnostics-1795193426305.txt`; build marker `A1_TRACKID_BETA5_RAMIL_AU_20261120`.

### What worked

- `BETA_OWNER_AUTO_START=ENABLED` / `ALREADY_ENABLED`: saved CELIKOM session auto-started successfully.
- `OWNER_ENABLED=ONE`: owner activation is present in the beta path.
- `DIAGNOSTIC_UI=ATTACHED`: the single status/TXT control is present. The BETA4 UI regression is no longer the blocker.
- `ISSUER_PROXY_HOOK_REGISTERED=ONE`, `ISSUER_PROXY_CREATED=ONE`: the early Retrofit proxy witness registered and observed one FileInfo/DownloadInfo proxy creation.

### First failed point — issuer method selection

The next counters are all zero:

- `ISSUER_METHOD_SELECTED=NONE`
- `ISSUER_HANDLER_INVOKE=NONE`
- `ISSUER_TRACKID=NONE`
- `EXACT_BETA_CREATOR=NONE`
- `ORIGINAL_SETTER=NONE`

The current `hookConcretePublisherTrackIdProxy()` implementation searches the loaded `FileInfoApi` / `DownloadInfoApi` interfaces for a declared method whose String/numeric parameter has Retrofit `@Query` or `@Path` with the exact value `trackId`. The proxy is seen, but this selection gate does not select a method in the real phone run. The diagnostic does **not** establish why it was rejected; do not guess whether the runtime method, annotation, interface/classloader or proxy shape differs. Because no method is selected, the concrete handler invocation is not observed and no original issuer Track ID reaches CELIKOM.

Downstream beta path is therefore not reached:

- `PREFETCH_STARTED=NONE`
- `SIGNED_MPEG_READY=NONE`
- `OWNER_RESOLVE_REQUEST=NONE`
- `GRANT_ADMITTED=NONE`
- `DECISION_ALTERNATE=NONE`
- `DATASOURCE_ARMED=NONE`
- `AUDIO_OPEN=NONE`
- `AUDIO_READ=NONE`

`EXACT_PREPARE=FEW` alone is not a replacement: there is no captured issuer ID, no admitted grant, and no armed alternate DataSource.

### Original Yandex playback and partial lineage evidence

- Original Exo counters: `EXO_FACTORY_CREATED=MANY`, `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`; `EXO_IO_FAILURE=NONE`. The original player continues reading audio normally.
- One `TCA_CREATOR_WRAPPER_FLOW_MATCH` and one `TCA_CREATOR_WRAPPER_ALBUM_LINK` were observed; `TCA_CREATOR_FLOW_LATER_SAME_TRACK=ONE` and `TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED=ONE`.
- This does not close the active native source chain: `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, descriptor/factory/source links are all `NONE`.
- The aggregate status explicitly remains `CELIKOM_REPLACEMENT=NOT_CONNECTED`.
- Renderer hooks are registered, but their registration and queue/sample-read counters do not prove a current-track replacement. Do not reopen renderer research while the earlier issuer-ID gate is still zero.

### Next implementation task — keep it narrow

1. Work only on the first failed gate: the real loaded FileInfo/DownloadInfo proxy method selection.
2. Inspect the actual runtime proxy interfaces and declared/inherited methods, exact Retrofit annotations, and classloader identity. Determine why the one created proxy does not yield `ISSUER_METHOD_SELECTED`.
3. Make the smallest fix that observes the exact original `trackId` argument inside the original request/Track scope and invokes the publisher handler exactly once unchanged. Do not capture arbitrary String/number arguments or broaden to unrelated APIs.
4. Add focused regression coverage for the actual runtime method shape and negative/unscoped calls. Run the relevant JVM and Android ARM13 CI.
5. Only after a real phone run captures `ISSUER_TRACKID`, continue down the existing chain in order: `EXACT_BETA_CREATOR` → `ORIGINAL_SETTER` → signed audio/grant → exact prepare → DataSource armed/open/read. Do not jump ahead or create another diagnostic-only APK.

**Do not ask the owner for another phone run until there is a concrete code correction with green CI and a clear expected counter change.** No AppMetrica investigation, broad DEX scans, new renderer probes, UI redesign or architecture reset.

**Preserve:** the single existing branch; NAV40/NAV45; Test.50; Windows; backend/production; the original publisher APK and its signer. Unknown or unapproved tracks must continue playing the original audio.
