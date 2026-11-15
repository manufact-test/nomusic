# CELIKOM Android A1 — exact Fp0 coroutine-resume identity checkpoint, 15.11.2026

**Stage A = NO-GO. Это не релиз и не CELIKOM audio replacement.** Единственная исследовательская ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Подтверждённая причина потери прежнего ThreadLocal-наблюдения

Из **оригинального издательски подписанного** Yandex 2025.10.4 #120.1gpr (6 DEX) независимая read-only CI проверка [#43695462019](https://github.com/manufact-test/nomusic/actions/runs/43695462019) вернула SUCCESS с:

- `fp0_resume_exact_same_continuation_static_proven=true`: точный `Fp0.<init>(Gp0,Oe2)` присутствует; `Fp0.invokeSuspend(Object)` вызывает `Gp0.new(Gp0, ru.yandex.music.data.audio.o, Oe2)`, и аргумент `Oe2` в этом call-site является **тем же this-объектом Fp0** (register-identity по DEX code_item, не эвристика).
- `fp0_resume_explicit_null_track_argument_static_proven=true`: **непосредственно перед этим invoke** точная инструкция DEX `const/4 0` записывает нулевой Track-argument register. Следовательно, возобновлённый `Gp0.new` уже не получает исходный Track через arg1. `Gp0.new` также создаёт Fp0 до потенциально приостанавливаемого `Hp0.const`, а `tCa` создаётся далее.
- `fp0_resume_track_binding_runtime_proven=false`. Это доказательство signed **статической структуры** и причины возможного обрыва прежнего scope, **не** доказательство реальной Track→tCa identity при воспроизведении.

## Что изменено

- **Код `6e409f9920c8ea0d47bf08d37d9da827bee89b2a`:** read-only hook точного конструктора `Fp0(Gp0,Oe2)` и слабая bounded `==` связь `Fp0 →` исходный Flow-Track, существующая только в памяти. При возобновлённом `Gp0.new` с `null` для Track восстановление допускается **исключительно** при совпадении исходного `Fp0` reference. Неизвестный, пропавший, повторно использованный для иного Track или конфликтующий continuation fail-closed.
- **Счётчики:** `NATIVE_TRACK_CONTINUATION_CONSTRUCTED`, `TRACK_CONTINUATION_RECOVERED`, `TRACK_CONTINUATION_CONFLICT`. Локальные Java тесты включают null/unknown/foreign/reentrant сценарии. Все реальные vendor methods по-прежнему исполняются один раз без подмены источника. Summary теперь 37 строк, последний статус `CELIKOM_REPLACEMENT;NOT_CONNECTED`.
- **Static audit `ef76b0879ebf67a09fc201087a6b825de5c17699` и `9efd2e802c54ee7a9079be6f28fd6354caa712ac`:** ограниченный скан Fp0 и жёсткая проверка replay того же continuation; явный нулевой аргумент проверяется отдельно, без чтения Track/URL/login/аудио.
- **Parser `495d37e3640f8c3e4ee3f7616f786835f0718bb0`:** новый `AUDIO_NATIVE_TRACK_CONTINUATION_HOOK` включён в PID-scoped отчёт; ранее он фактически не учитывался парсером, поэтому четыре REGISTERED не могли служить доказательством пятого hook.
- **Независимые резервы:** `backup/android-a1-track-continuation-pre-identity-20261115` @ `d01849b2cdbd5af5c5337d058c1ba55e460412db` (до runtime кода); `backup/android-a1-fp0-static-audit-pre-ci-20261115` @ `6e409f9920c8ea0d47bf08d37d9da827bee89b2a`.

## Проверки

- [Clone-only ARM13 #43694941351](https://github.com/manufact-test/nomusic/actions/runs/43694941351): **SUCCESS**. Java regression, scoped module, true Android 13 ARM, 25/25 stable lifecycle. Original publisher в этом clone-only прогоне не тестировался.
- [Publisher-first ARM13 #43694941316](https://github.com/manufact-test/nomusic/actions/runs/43694941316): **SUCCESS**, оригинал + клон одновременно, `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. Нет login, audio, current selected track/edition/generation, decoder-before-prepare.
- [Exact signed Fp0 audit #43695269210](https://github.com/manufact-test/nomusic/actions/runs/43695269210) и [zero Track argument audit #43695462019](https://github.com/manufact-test/nomusic/actions/runs/43695462019): **SUCCESS**.
- Пятый hook в ограниченном парсере проверяется отдельным повторным CI [#43695595723](https://github.com/manufact-test/nomusic/actions/runs/43695595723) и [#43695595735](https://github.com/manufact-test/nomusic/actions/runs/43695595735). На момент создания файла итог ещё требуется проверить.

## Следующее

1. Проверить новый `AUDIO_NATIVE_TRACK_CONTINUATION_HOOK` в clone-only и publisher-first **как registration event**, не как proof of execution.
2. На следующей **добровольно предоставленной** owner-диагностике изучать `NATIVE_TRACK_SOURCE_REQUEST`, `NATIVE_TRACK_CONTINUATION_CONSTRUCTED`, `TRACK_CONTINUATION_RECOVERED`, `TRACK_WRAPPER_LINK`, затем `WRAPPER_MAIN_SOURCE → WRAPPER_DESCRIPTOR_LINK → TRACK_DESCRIPTOR_FACTORY_LINK → TRACK_FACTORY_SOURCE_LINK → TRACK_SOURCE_OPEN_LINK → TRACK_SOURCE_READ_LINK`.
3. `download2.o.for` может отдельно прерываться coroutine. Если для него не доказана wrapper-scope, не соединять с descriptor по строкам или совпадению времени. Разбирать только exact, bounded и privacy-safe identity по подписанному DEX.
4. **Никаких установок пользователю**, APK релиза, отключения Play Protect, login/аккаунта, подмены native audio и изменений Test.50, frozen A1, Windows, extension, backend/API/production до реальных доказательств.
