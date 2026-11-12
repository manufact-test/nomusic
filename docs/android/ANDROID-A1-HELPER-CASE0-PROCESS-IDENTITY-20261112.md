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

**Заполнить после завершения native CI**, до этого `NO_GO`. Test.50, frozen A1, vendor SDK/exceptions, ключи, авторизация, production, Windows и handset не изменяются.
