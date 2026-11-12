# CELIKOM A1 — helper B CASE_0 process identity, 12.11.2026

**Issue:** [#47](https://github.com/manufact-test/nomusic/issues/47). Branch: `experiment/android-a1-helper-process-identity-case0-arm13-20261112`; exact start `77cf1b09ca6bad77cc8a384293fea68b67654e46`.

## Одно проверяемое предположение

На прежнем no-suppression ARM13 original 25/25 и clone 1/25 read-only `legacy Push` helper `CASE_0` вернул **FALSE 2/2**. Проверяем **только** следующее: является ли этот `FALSE` ошибочной классификацией текущего MAIN после package namespace rewrite? `FALSE` **не является доказательством ошибки** без точного контракта метода и входных значений. Базовые service lifecycle, modern activation и nullable direct fields не повторять.

## Независимые технические свидетельства

- `android/a1-process-identity-helper/case0.py` повторно проверяет точный SHA256/размер приватного publisher XAPK 2025.10.4; импортирует неизменённый private DEX reader A, берёт **CASE_0 строго по прежней sorted exact-guard-target логике** и проверяет только её direct + one-hop Android process-name suppliers, package suppliers, String.equals, ограниченную форму условных веток, прямые stock/clone literals. Возвращает конечные классификации, **не** имена исходных классов/строки/DEX.
- Для честности: если найден `IF_EQZ/NEZ`, это **не полное доказательство семантики Boolean возвращаемого значения**; `actual_meaning_of_false=UNKNOWN`, пока не подтверждены точная ветка и роли. Никаких SDK predicate overrides.
- Отдельный CI копирует собственный read-only LSPatch witness A во временный каталог `RUNNER_TEMP`; создаёт генерируемые private target Java **только** в этой временной копии. Исходные файлы A в репозитории не модифицирует.
- Через импорт проверенного native launcher A выполняет **original-first** реальные ARM Android13 75 секунд/25 сэмплов с несдержанным фатальным исключением. Разрешена только в-памяти замена `lead.BRANCH` на выделенный helper branch: остальная логика A оригинальная.
- Для stock и clone сравнивает реально активный MAIN процесса по `ps -A`, события `am_proc_start/bound/died` и `Application` / `MainScreenActivity` manifest process. Отдельно берёт уже существующее read-only CASE_0 state из зарегистрированного hook clone. **Stock CASE_0 в JVM не наблюдается данным сценарием, поэтому `UNKNOWN`; не приписывать ему TRUE.**

## Приёмка

Только полная causal attribution: доказано ли, что конкретный CASE_0 сравнивает текущую роль MAIN и выдаёт ошибочный результат вследствие package namespace? Если нет — честный ограниченный негативный результат, без случайной config правки. Тесты и CI в своей зоне, один PR для главного на ревью, без merge. Green unit/static не равен Stage A PASS.

## Настоящий ARM13

## Проверенное точное ARM13 — #43300683112 (закрытие единственной гипотезы)

**Actual CI**: https://github.com/manufact-test/nomusic/actions/runs/43300683112  
**Точный TESTED source**: `87d1feda69fcfeb078bb421e0a73bbeb3fa20ccd`  
**Точный резерв executable source**: `backup/android-a1-helper-case0-exact-tested-20261112` @ `87d1feda69fcfeb078bb421e0a73bbeb3fa20ccd`. Отчётный коммит после фактического прогона исполняемый код не меняет.

**Успешные технические стадии:** все пять B-only synthetic regressions PASS; точный оригинальный XAPK 2025.10.4 верифицирован SHA256/размером, прочитаны 6 DEX, приватные target names сгенерированы только во временной копии read-only модуля, модуль собран, настоящий ARM Android13 (ARM64+ARMv7) загружен. Установка оригинала издателя (16 splits) **первой**, отдельный CELIKOM ONE-APK рядом. Весь тест **без exception suppression/SDK changes**.

**Точное статическое исследование CASE_0**:
- Тот же метод, что в предыдущем `PrivatePushTargets.getAllFatalGuardExactTargets()` после сортировки и с учётом точной Java-сигнатуры; соответствующий исходный метод с телом найден ровно один раз, Boolean return.
- Локальный DEX контролируется: нет `ru.yandex.music` / CELIKOM package literal; нет прямого Android `getProcessName`/ `getPackageName` / `myPid` или `String.equals` в теле CASE_0, нет их прямых вызовов на 1 hop; локальные IF_EQZ и IF_NEZ; 2 return instructions.
- Существующий консервативный DEX evaluator при синтетических длинах `[0,1,2,4,8,16,32,64,128]` дал **`TRUE_FOR_ZERO_ONLY`**. Значит на покрытом подмножестве инструкций CASE_0 соответствует **проверке на пустую строку**, а **FALSE при непустом имени процесса — ожидаемое значение**, не свидетельство ошибки MAIN. Этот эксперимент не доказывает, что конкретный runtime аргумент был именем процесса; actual argument/private symbols не записывались.
- **Stock CASE_0 внутри JVM не измерен**, остаётся `UNKNOWN`. Нельзя утверждать, что он там TRUE.

**Живой ARM13 оригинал vs клон:**

| Критерий | Stock publisher | CELIKOM one-APK |
|---|---|---|
| Application `android:process` | DEFAULT | DEFAULT |
| Native MainScreenActivity `android:process` | DEFAULT | DEFAULT |
| Собственный MAIN PID присутствует в `ps -A` | YES | YES |
| Собственный AUX/Metrica PID виден | YES | YES |
| ActivityManager `am_proc_start` MAIN | 1 | 3 |
| ActivityManager `am_proc_bound` MAIN | 1 | 3 |
| ActivityManager `am_proc_died` MAIN | 0 | 3 |
| 75s/25 foreground MAIN acceptance | **25/25** | **1/25** |
| CASE_0 B-only read-only clone hook | **UNKNOWN** | **2 ENTER, 2 FALSE, 0 TRUE, 0 THROW** |
| Original `SDK_PUSH DETAIL_NOT_INITIALIZED` | не возникает в baseline | снова возникает |
| Suppressed original exceptions | 0 | 0 |

**Вердикт — NEGATIVE / CLOSED FOR THIS SPECIFIC HYPOTHESIS.** Система Android правильно называет собственный главный процесс CELIKOM; в манифесте оригинала и клона одинаково default process. Точный CASE_0 **не выглядит отдельным сравнением MAIN с именем исходного пакета**, возвращает FALSE на проверке непустого String (для синтетических входов). Таким образом **ошибка process namespace или CASE_0 FALSE как причина фатального Push не доказана**. Нельзя добавлять override TRUE, переименовывать Android process или патчить SDK.

**Ограничения:** Android host не даёт значение Java аргумента CASE_0, stock in-JVM CASE_0 нет; DEX evaluator покрывает только поддержанные инструкции и тестовые длины, не весь runtime. Отрицательный вывод не означает, что внутреннее состояние Push исправно. Последующее исследование другой вложенной зависимости — у A; B его не повторяет.

**Факт CI:** итог native job **FAIL по продуктовому критерию**, так и должно быть при текущем clone 1/25. Это не unit/static PASS на весь продукт. Stage A **NO-GO** / Stage B **LOCKED**. Никакого собственного исправления не предложено без доказанного дефекта. Всё только в 4 файлах B, A и frozen/Test.50/production не тронуты, бинарники/ключи/private symbols не публиковались.
 Test.50, frozen A1, vendor SDK/exceptions, ключи, авторизация, production, Windows и handset не изменяются.
