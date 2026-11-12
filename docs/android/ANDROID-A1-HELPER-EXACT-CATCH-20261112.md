# CELIKOM Android A1 — независимый помощник B: точные DEX try/catch в Push.impl.a

Дата: 12 ноября 2026. Issue [#50](https://github.com/manufact-test/nomusic/issues/50). Стартовый SHA `9460b8417f518ff380bd5ceeeeb101ad60b70d5d`. Собственная ветка `experiment/android-a1-helper-exact-try-handler-arm13-20261112`.

## Проверяем только одну гипотезу

На реальном native ARM13 в том же вызове `Push.impl.a` near-helper вернул `TRUE`, после чего метод напрямую завершился `SDK_PUSH DETAIL_NOT_INITIALIZED`. В статическом обычном CFG именно `TRUE` не достигает моделируемой строки ошибки / `throw` (source-only [#43299938004](https://github.com/manufact-test/nomusic/actions/runs/43299938004)); в точном DEX данного метода `HAS_TRY_ITEMS` ([#43300836622](https://github.com/manufact-test/nomusic/actions/runs/43300836622)). Проверка B: могло ли **только дополнительное исключительное ребро** объяснять расхождение, и какой тип исключений оно действительно перехватывает?

**Принципиальное разделение:** `near-helper` уже **вернулся TRUE**, следовательно, нельзя объяснять наблюдаемый впоследствии `throw` его собственной ошибкой при этом же успешном возвращении. Отдельно смотрим `catch` вокруг *последующих* вызовов на успешной ветке `TRUE`.

## Метод анализа

1. Только конкретный publisher-signed XAPK 2025 из existing private temporary draft release. Сначала подтверждаются точный размер и SHA256, затем оригинальный A DEX-reader посредством импорта без правок. Имя класса, метод/поле, сырая строка и байт-код остаются внутри ephemeral CI.
2. Выбирается только та перегрузка `Push.impl.a`, для которой тот же A-классификатор возвращает `TRUE_CFG_BLOCKS_THROW`, с источником `private_exclusive_fatal_guard_refs`. При отсутствии **ровно одного** совпадения — `UNKNOWN`.
3. Строго считываются `code_item`, его выравнивание, `try_item` в code units, `encoded_catch_handler_list`, signed-size SLEB128, ULEB128 типы и адреса. Валидируются границы, цель, совпадение с декодированным набором инструкций, ограничение количества и непротиворечивость диапазонов. Неподдержанные случаи — `UNKNOWN`.
4. Обычный CFG берётся из существующего `_nexts` A, не расширяется предположениями. После успешной ветки `TRUE` ищутся достижимые **последующие invoke**. Для каждого, лежащего в `try`, отдельно устанавливается возможность перехода в обработчик и из обработчика в конкретный моделируемый `throw`.
5. `catch-all` и точный `Throwable` дают структурно универсальный тип обработчика. `catch(Exception/RuntimeException/IllegalStateException)` и прочие typed-handlers **не объявляются причинно совпадающими с исключением живого приложения** без фактической проверки класса; при достижимом обработчике они дают `UNKNOWN` в главном вердикте.
6. `TRY_COVERS_THROW_BUILD` отвечает, охватывает ли один `try_item` обе инструкции: загрузку исходной строки ошибки и сопоставленный `throw`; это структурная классификация, не доказательство формирования именно этого экземпляра Throwable. Отдельно указывается, есть ли в TRUE-ветке буквально названный SDK `init/activate`; произвольная obfuscated функция не объявляется методом инициализации.

## Разрешённые ответы и жёсткие ограничения

- `EXACT_HELPER_IN_TRY` / `NOT_IN_TRY` / `UNKNOWN`.
- `EXACT_THROW_IN_HANDLER_REACH` / `NOT_REACH` / `UNKNOWN`.
- `TRY_COVERS_THROW_BUILD` / `NOT` / `UNKNOWN`.
- Дополнительные конечные семейства: тип `catch`; `TRUE_PATH_INVOKE_CATCH_REACH`, `HELPER_OWN_HANDLER_REACH`, `SDK_INIT_NEARBY_IN_TRY`, `true_normal_cfg`.

Это **не доказательство фактической работы handler в JVM**, не говорит, какой исключительный объект выброшен, и не свидетельствует о достижении runtime ветки. A исследует runtime независимо. Никакого patch, инверсии guard, suppression, перезапуска sdk или переименования процессов.

Исполняемые B-only файлы: `android/a1-exact-catch-helper/exact_catch.py`, `test_exact_catch.py`; B-only workflow: `.github/workflows/android-a1-helper-exact-catch.yml`. Ни один файл `android/native-yandex-hooklab/**` не меняем. Продукт **Stage A NO-GO, Stage B LOCKED**, даже при зелёном static CI.

## Итоги точного private CI

Результат [#43305541822](https://github.com/manufact-test/nomusic/actions/runs/43305541822) и его ограничения записать здесь после завершения прогона.
