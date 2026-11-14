# CELIKOM Android A1 — Track → Exo identity evidence hardening (15.11.2026)

**Исследовательский код, не релиз. Stage A = NO-GO.** Продолжение существующего одноплеерного native Yandex A1, без подмены источника. Исходный Android, Test.50, frozen A1, Windows, extension, backend и production не затронуты. Владелец ничего не устанавливает.

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

После изменения исходников запущены [clone-only ARM13 #43654168986](https://github.com/manufact-test/nomusic/actions/runs/43654168986) и [AppMetrica lifecycle ARM13 #43654169076](https://github.com/manufact-test/nomusic/actions/runs/43654169076). Clone-only #43654168986 завершён **SUCCESS**, 25/25 на свежем Android 13 ARM, JVM и module checks green. Publisher и реальное audio отсутствовали. Publisher-first #43654169076 ещё выполняется; его результат не переносить на Stage A. Исходные `#43649573590` SUCCESS / 25-25 относятся к **предыдущему checkpoint** `d8049537`, а не к `f7983590`. Нельзя переносить этот статус на новые исходники.
