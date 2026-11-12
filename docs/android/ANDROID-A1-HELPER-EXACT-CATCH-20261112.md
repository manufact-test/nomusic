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

### Проверка выполнена на точном исходнике

**Проверенный статический GitHub Actions [#43305541822](https://github.com/manufact-test/nomusic/actions/runs/43305541822)** — весь job **SUCCESS**. Исполняемый исходник конкретного прогона: `3f84b235faaf5a63a9db9ecea7e5fed72b3ea2a7`. Неизменяемый резерв точного проверенного кода: `backup/android-a1-helper-exact-catch-tested-static-20261112` @ `3f84b235faaf5a63a9db9ecea7e5fed72b3ea2a7`. Содержимое XAPK сравнивалось с точным оригиналом (45961661 байт, SHA256 из A's private reader), проверка выполнена в эфемерной CI среде; бинарники в артефакты не загружали, очистка завершилась успешно.

**8 собственных синтетических тестов PASS**, в том числе:
- инъекция исключительного ребра после `TRUE` в `catch-all` при отсутствии обычного пути к `throw`;
- адреса/выравнивание/границы `try_item` и `handler_off`; неизвестная запись — fail closed;
- `catch(Throwable)` и произвольный typed `catch` не смешиваются: для последнего при достижимости — `UNKNOWN` до подтверждения runtime типа;
- метод без `try` и обработчика не имеет ложного пути.
**13 исходных регрессионных тестов A PASS**. Компиляция helper и точный статический анализ прошли. Никакой Android guest, APK-клон или пользовательское устройство не запускались: они не нужны для этой задачи B.

### Результат для точной падающей перегрузки

| Категория | Доказанное значение |
|---|---|
| Exact selected candidate | **ONE_EXACT_TARGET** |
| Общее число `try_item` | **5** |
| `EXACT_HELPER_IN_TRY` | **EXACT_HELPER_IN_TRY** |
| `HELPER_OWN_HANDLER_REACH` | **EXACT_THROW_IN_HANDLER_REACH** |
| `TRUE_PATH_INVOKE_CATCH_REACH` | **EXACT_THROW_IN_HANDLER_REACH** |
| `EXACT_THROW_IN_HANDLER_REACH` | **EXACT_THROW_IN_HANDLER_REACH** |
| `TRY_COVERS_THROW_BUILD` | **TRY_COVERS_THROW_BUILD** |
| Существующие группы обработчиков | **CATCH_ALL**, **TYPED_EXCEPTION** |
| Literally named SDK `init/activate` on TRUE path | **NO_EXACT_INIT_CALL** |
| Проверка обычного (без `catch`) CFG | **TRUE_NORMAL_BLOCKS_THROW** |
| Фактический переход в handler во время запуска | **NOT OBSERVED** |

**Вердикт одной гипотезы: STRUCTURALLY POSSIBLE.** Нормальный CFG исключает достижение конкретного моделируемого `throw` после `TRUE`. Однако как минимум один другой `invoke`, доступный *после* `TRUE`, находится под обработчиком, из которого этот `throw` достижим; маршрутизация с универсальным `catch-all` допускает исключительное ребро. Таким образом неполный граф **может** объяснять статическое/runtime противоречие; повторной проверки CASE_0 или сервисов не требуется.

**Не доказано:** какой именно последующий `invoke` выбрасывает какое исключение на живом ARM13, происходит ли такой переход вообще, соответствует ли построенный `throw` реальному стеку. Собственный успешный near-helper не мог одновременно вернуть `TRUE` и выбросить исключение в том же вызове; вариант с его **собственным** handler не является причинным объяснением наблюдаемой последовательности. Typed `catch(Exception)` отдельно не доказывает захват конкретного SDK Throwable; универсальный `catch-all` даёт только структурную возможность. Произвольные obfuscated вызовы нельзя объявлять SDK `init`.

**Передать главному разработчику A:** точный статический граф оправдывает *проверку* исключительного перехода после TRUE; A отдельно определяет реально выбросивший вызов/тип и handler на Android. Никаких правок SDK/подмены Boolean/подавления исключения. **Static CI SUCCESS ≠ product PASS**. Stage A **NO-GO**, Stage B **LOCKED**; Test.50, frozen A1, Windows, extension, прод, мобильное устройство и A-owned файлы не тронуты.
