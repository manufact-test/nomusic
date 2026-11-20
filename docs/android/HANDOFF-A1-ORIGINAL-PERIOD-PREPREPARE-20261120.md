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
